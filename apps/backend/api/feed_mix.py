import itertools
import random
from collections import defaultdict, deque
from datetime import datetime

from api.add_senders import add_senders
from api.page_response import PageResponse, Sender
from crawler.prismac import pg_client
from crawler.recommendation.embedding import generate_feed_from_page
from prisma import Prisma
from prisma.models import Comment, Message, Page

SUPERSTACK_RECEIVER_ID = '4ee604f3-987d-4295-a2fa-b58d88e5b5e0'


async def find_user(client: Prisma, userid: str):
    # Check if the user exists
    existing_user = await client.user.find_first(where={"id": userid})

    if existing_user:
        # User already exists
        return existing_user


async def _process_messages(messages: list[Message]):
    grouped_messages: dict[str, list[Message]] = defaultdict(list)
    for m in messages:
        group_key = m.page_id or m.url
        grouped_messages[group_key].append(m)

    page_ids_to_fetch = set(
        [m.page_id for m in messages if m.page_id is not None])

    pages = pg_client.get_pages_by_id(list(page_ids_to_fetch))

    pages = {p.id: p for p in pages}

    result: list[PageResponse] = []

    for m in grouped_messages:
        r = grouped_messages[m][0]
        if r.page_id is not None:
            page = pages.get(r.page_id)

            # The page has been deleted from server.henryn.ca DB
            if page is None:
                continue

            page_response = PageResponse.from_prisma_page(page)
        else:
            # should not happen currently | we really should not reach here...
            raise ValueError("URLs not supported yet")

        page_response.senders = [Sender.from_message(
            m) for m in grouped_messages[m]]
        result.append(page_response)

    return result, pages


async def get_inbox_messages(client: Prisma, user_id: str) -> list[Message]:
    messages = await client.message.find_many(order={'sent_on': 'desc'}, include={'sender': True, 'receiver': True},
                                              where={
                                                  'receiver_id': str(user_id)
    })

    return messages


async def get_friend_comments(client: Prisma, user_id: str | None) -> list[Comment]:
    # Query for comments made by users who are not the same as the user with the given user_id
    friend_comments = await client.comment.find_many(
        where={
            # "author_id": {"not": user_id},
            "is_deleted": False
        },
        # Ensure only distinct page_id values are returned
        distinct=["page_id"]
    )

    # Extract the page_id values from the comments
    return friend_comments


async def get_friend_activity(client: Prisma, user_id: str | None) -> list[Message | Comment]:
    """Comments and broadcasts"""
    friend_comments = await get_friend_comments(client, user_id)

    return friend_comments


async def get_similar_articles(client: Prisma, user_id: str) -> list[PageResponse]:
    user = await find_user(client, str(user_id))

    # Get a random sample of pages the user has liked
    liked_pages = await client.likedpage.find_many(take=100, where={
        'user_id': user.id
    })

    liked_page_ids = set([lp.page_id for lp in liked_pages])

    # Select K random pages to generate feed from
    selected_liked_pages = random.choices(
        liked_pages, k=min(20, len(liked_pages)))

    if len(selected_liked_pages) == 0:
        print(f'User {user_id} has no liked pages')
        return []

    similar: list[PageResponse] = []

    liked_pages = pg_client.get_page_stubs_by_id(
        [lp.page_id for lp in selected_liked_pages])
    for lp in liked_pages:
        similar.extend(await generate_feed_from_page(lp.url))

    # Since some articles might be similar to multiple articles that the user liked, we need to deduplicate
    # If something shows up multiple times, it's score increases (matches person's interests more)
    # Map page_id -> PageResponse
    similar_grouped: dict[int, PageResponse] = {}

    for s in similar:
        if s.id in similar_grouped:
            # Add one to "bonus" matching multiple of their liked stuff
            similar_grouped[s.id].score += s.score + 1
        else:
            similar_grouped[s.id] = s

    similar_final = list(similar_grouped.values())
    await add_senders(client, similar_final)

    # TODO: shuffle this list so that users get a diverse representation of their interests, rather than just highest score
    similar_final.sort(key=lambda x: x.score, reverse=True)
    return similar_final


async def random_feed(client: Prisma) -> list[PageResponse]:
    limit = 60
    current_datetime = datetime.now()

    # Format it as "YYYY-MM-DD"
    seed = current_datetime.strftime("%Y-%m-%d") + 'A'

    random_pages = pg_client.query("""
        WITH random_ids AS (SELECT id, MD5(CONCAT(%s::text, content_hash)) FROM "Page" ORDER BY md5 LIMIT 300)
        SELECT p.* From "Page" p INNER JOIN random_ids ON random_ids.id = p.id WHERE p.depth <= 1 ORDER BY COALESCE(page_rank, 0) DESC LIMIT %s
        """, [seed, limit])

    random_pages = [Page(**p) for p in random_pages]
    pages = [PageResponse.from_prisma_page(p) for p in random_pages]

    await add_senders(client, pages)

    return pages


async def page_ids_to_page_response(client: Prisma, ids: list[int]) -> list[PageResponse]:
    pages = pg_client.get_pages_by_id(ids)
    pages_filled = [PageResponse.from_prisma_page(p) for p in pages]

    await add_senders(client, pages_filled)

    return pages_filled


async def mix_feed(client: Prisma, user_id: str | None) -> list[PageResponse]:
    """
    The whole mixer should be cached once per day

    inbox messages
    friend’s activity (comments, broadcasts)


    similar articles from saved articles list
    random_pages (global)

    :param user_id:
    :return:
    """

    # Get inbox messages for the user
    inbox_messages: list[Message] = await get_inbox_messages(client, user_id) if user_id is not None else []

    inbox_messages: list[PageResponse] = await page_ids_to_page_response(client, [x.page_id for x in inbox_messages])

    # Get friend activity, which includes comments and broadcasts
    friend_activity: list[Message | Comment] = await get_friend_activity(client, user_id)

    friend_activity: list[int] = [x.page_id for x in friend_activity][0:70]

    # inbox_messages = await page_ids_to_page_response(client, [x.page_id for x in inbox_messages])
    friend_activity: list[PageResponse] = await page_ids_to_page_response(client, friend_activity)

    # Get similar articles based on the user's liked pages
    similar_articles = await get_similar_articles(client, user_id) if user_id is not None else []

    # Get random pages from the global pool
    random_articles = await random_feed(client)

    # Combine and shuffle the feeds
    combined_feed = {
        'inbox': deque(inbox_messages),
        'friend': deque(friend_activity),
        'similar': deque(similar_articles),
        'random': deque(random_articles)
    }

    feed_order = itertools.cycle(['inbox', 'friend', 'similar', 'random'])
    resulting_feed = []

    for ty in feed_order:
        if len(resulting_feed) > 60:
            break
        if len(combined_feed) == 0:
            continue
        if ty not in combined_feed:
            continue
        if len(combined_feed[ty]) == 0:
            del combined_feed[ty]
            continue

        resulting_feed.append(combined_feed[ty].popleft())

    # Return the mixed feed to the user
    return resulting_feed
