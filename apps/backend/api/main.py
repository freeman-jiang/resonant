import asyncio
import os
import random
from collections import defaultdict
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

import pytest
from api.page_response import PageResponse, Sender
from crawler.link import Link, clean_url
from crawler.prismac import PostgresClient, pg_client
from crawler.recommendation.embedding import (NearestNeighboursQuery,
                                              _query_similar,
                                              generate_feed_from_page,
                                              store_embeddings_for_pages)
from crawler.worker import crawl_interactive, crawl_only, get_window_avg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
from prisma.models import Comment, Message, Page, User
from pydantic import BaseModel, validator

from .add_senders import add_senders, get_senders_for_pages
from .feed_mix import (SUPERSTACK_RECEIVER_ID, _process_messages,
                       get_inbox_messages, mix_feed, page_ids_to_page_response)

load_dotenv()

app = FastAPI()
client = Prisma(datasource={'url': os.environ['DATABASE_URL_SUPABASE']})

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://app-superstack.vercel.app",
    "https://resonant.vercel.app",
    "https://www.resonant.live",
    "https://resonant.live"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    print("Connecting to database...")
    await client.connect()
    pg_client.connect()


async def find_user(userid: str):
    # Check if the user exists
    existing_user = await client.user.find_first(where={"id": userid})

    if existing_user:
        # User already exists
        return existing_user


class FindPageRequest(BaseModel):
    url: str
    userId: Optional[str]

    @validator("url")
    def check_url(cls, v: str):
        Link.from_url(v)
        return v


# to hide email
class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    profile_picture_url: Optional[str]

    @classmethod
    def from_user(cls, user: User):
        return UserResponse(id=user.id, first_name=user.first_name, last_name=user.last_name,
                            profile_picture_url=user.profile_picture_url)


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    upvotes: int
    is_deleted: bool
    children: list['CommentResponse']

    @classmethod
    def from_comment(cls, comment: Comment):
        assert (comment.author)

        # Until the SQL statement gets the recursion properly this does nothing
        children: list[CommentResponse] = []
        if comment.children:
            # recurse
            children = [CommentResponse.from_comment(c)
                        for c in comment.children]

        if comment.is_deleted:
            return CommentResponse(id=comment.id, content="[deleted]", created_at=comment.created_at,
                                   updated_at=comment.updated_at, author=UserResponse(
                                       id="", first_name="", last_name="", profile_picture_url=""),
                                   upvotes=comment.upvotes, is_deleted=comment.is_deleted, children=children)

        return CommentResponse(id=comment.id, content=comment.content, created_at=comment.created_at,
                               updated_at=comment.updated_at, author=UserResponse.from_user(
                                   comment.author),
                               upvotes=comment.upvotes, is_deleted=comment.is_deleted, children=children)


class FindPageResponse(BaseModel):
    page: PageResponse
    has_broadcasted: bool
    type: str = "page"
    comments: list[CommentResponse]
    num_comments: int
    outbound_urls: list[str]


@app.get('/recommended')
async def recommend(userId: UUID) -> list[PageResponse]:
    """
    Get a random sample of similar pages from the pages user has already liked from LikedPage
    :param userid:
    :return:
    """
    user = await find_user(str(userId))

    # Get a random sample of pages the user has liked
    liked_pages = await client.likedpage.find_many(take=100, where={
        'user_id': user.id
    })

    liked_page_ids = set([lp.page_id for lp in liked_pages])

    # Select K random pages to generate feed from
    selected_liked_pages = random.choices(
        liked_pages, k=min(10, len(liked_pages)))

    if len(selected_liked_pages) == 0:
        print(f'User {userId} has no liked pages')
        return []

    similar: list[PageResponse] = []

    liked_pages = pg_client.get_page_stubs_by_id(
        [lp.page_id for lp in selected_liked_pages])
    for lp in liked_pages:
        similar.extend(await generate_feed_from_page(lp.url))

    # Since some articles might be similar to multiple articles that the user liked, we need to deduplicate
    # If something shows up multiple times, it's score increases (matches person's interests more)
    # Map page_id -> PageResponse
    similar_grouped: dict[str, PageResponse] = {}

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


@app.get('/liked/{userid}')
async def get_liked_pages(userid: str) -> list[PageResponse]:
    lps = await client.likedpage.find_many(take=100, where={
        'user_id': userid,
    })

    # sort by most recent
    lps.sort(key=lambda x: x.created_at, reverse=True)
    page_ids = [lp.page_id for lp in lps]

    pages = pg_client.get_pages_by_id(page_ids)
    # sort by most recent
    pages.sort(key=lambda x: page_ids.index(x.id))

    return [PageResponse.from_prisma_page(p) for p in pages]


@app.get("/like/{userid}/{pageid}")
async def like(userid: str, pageid: int) -> None:
    page = pg_client.get_page(id=pageid)

    if page is None:
        raise HTTPException(400, "Page does not exist")

    user = await find_user(userid)
    if not user:
        raise HTTPException(400, "User does not exist")

    await upsert_liked_page(page, user)
    # urls = await generate_feed_from_page(page.url)

    # print("Recommended", urls)
    return None


@app.delete("/unlike/{userid}/{pageid}")
async def unlike(userid: str, pageid: int) -> None:
    user = await find_user(userid)
    if not user:
        raise HTTPException(400, "User does not exist")

    lp = await client.likedpage.find_first(where={
        'page_id': pageid,
        'user_id': userid
    })

    if lp is None:
        raise HTTPException(400, "Page is not liked")

    await client.likedpage.delete(where={
        'id': lp.id
    })
    return None


async def _broadcast(user: User, page: Page):
    message = await client.message.find_first(where={
        'page_id': page.id,
        'sender_id': user.id,
        'receiver_id': SUPERSTACK_RECEIVER_ID,
    })
    if message is None:
        await client.message.create(data={
            'page_id': page.id,
            'sender_id': user.id,
            # Hardcode superstack.app@gmail.com ID for global shares
            'receiver_id': SUPERSTACK_RECEIVER_ID,
        })


async def upsert_liked_page(page: Page, user: User):
    """
    Adds the LikedPage for the given user and page or does nothing if it already exists
    :param page:
    :param user:
    :return:
    """
    lp = await client.likedpage.find_first(where={
        'user_id': user.id,
        'page_id': page.id,
    }, include={})
    if lp is None:
        await client.likedpage.create(data={
            'user': {
                'connect': {
                    'id': user.id
                }
            },
            'page_id': page.id
        })


class SearchQuery(BaseModel):
    url: Optional[str]
    query: Optional[str]

    def __init__(self, **data: dict[str, str]):
        if 'query' not in data and 'url' not in data:
            raise ValueError("Must provide either 'query' or 'url'")
        super().__init__(**data)

    @validator("query")
    def check_valid_query(cls, v: str):
        if not v:
            raise ValueError("Query must not be empty string")
        return v

    @validator("url")
    def check_url(cls, v: str):
        Link.from_url(v)
        return v


@app.post("/search-topic")
async def search_topic(body: SearchQuery) -> list[PageResponse]:
    """
    Exact same as /search endpoint, but shuffles the PageResponse for each day to have new articles for each feed.
    :param body:
    :return:
    """
    pass


@app.post("/search")
async def search(body: SearchQuery) -> list[PageResponse]:
    if body.url:
        url = body.url
        print("Searching for similar URLs to", url)

        contains_url = pg_client.query(
            'SELECT 1 FROM "Page" p INNER JOIN Embeddings e ON p.url = e.url WHERE p.url = %s', [url])

        if contains_url:
            print("Found existing URL!")
            query = NearestNeighboursQuery(url=url)
        else:
            print("Crawling this URL")
            want_vec, _ = await crawl_interactive(Link.from_url(url))
            query = NearestNeighboursQuery(vector=want_vec, url=url)

        similar = _query_similar(query)

    else:
        want_vec = get_window_avg(body.query)
        query = NearestNeighboursQuery(vector=want_vec, text_query=body.query)
        similar = _query_similar(query)

    await add_senders(client, similar)

    return similar


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get('/random-feed')
async def random_feed(limit: int = 60) -> list[PageResponse]:
    """
    Gets a random set of Pages with depth <= 1, based on the seed.
    We calculate the MD5 of (seed + content_hash), then get the first X elements with the highest MD5.
    Whenever we have a new seed, there will be a completely new set of pages.

    Seed is currently calculated as current YYYY-MM-DD.
    """
    # seed = str(random.randint(0, 100))
    # Get the current date and time
    current_datetime = datetime.now()

    # Format it as "YYYY-MM-DD"
    seed = current_datetime.strftime("%Y-%m-%d") + 'A'

    random_pages = pg_client.query("""
    WITH random_ids AS (SELECT id, MD5(CONCAT(%s::text, content_hash)) FROM "Page" ORDER BY md5 LIMIT 5000)
    SELECT p.* From "Page" p INNER JOIN random_ids ON random_ids.id = p.id WHERE p.depth <= 1 ORDER BY COALESCE(page_rank, 0) DESC LIMIT %s
    """, [seed, limit])

    random_pages = [Page(**p) for p in random_pages]
    pages = [PageResponse.from_prisma_page(p) for p in random_pages]

    await add_senders(client, pages)

    return pages


@app.post('/share/{user_id}/{page_id}')
async def share_page(user_id: str, page_id: int) -> None:
    page = pg_client.get_page(id=page_id)

    if page is None:
        raise HTTPException(400, "Page does not exist")

    user = await find_user(user_id)
    if not user:
        raise HTTPException(400, "User does not exist")

    await _broadcast(user, page)
    return None


@app.post('/unshare/{user_id}/{page_id}')
async def unshare_page(user_id: str, page_id: int) -> None:
    user = await find_user(user_id)
    if not user:
        raise HTTPException(400, "User does not exist")

    message = await client.message.find_first(where={
        'page_id': page_id,
        'sender_id': user.id,
        'receiver_id': '4ee604f3-987d-4295-a2fa-b58d88e5b5e0',
    })

    if not message:
        raise HTTPException(400, "Message does not exist")

    await client.message.delete(where={
        'id': message.id
    })
    return None


class SendMessageRequest(BaseModel):
    senderId: str
    pageId: int
    receiverId: str
    url: Optional[str]
    message: Optional[str]

    # TODO: add back validations for uuid and stuff


class AlreadyAdded(BaseModel):
    type: str = "already_added"
    url: str


class ShouldAdd(BaseModel):
    type: str = "should_add"
    url: str


class UrlRequest(BaseModel):
    url: str

    @validator("url")
    def check_url(cls, v: str):
        Link.from_url(v)
        return v


@app.post('/search_url')
async def search_url(body: UrlRequest) -> Union[ShouldAdd, AlreadyAdded]:
    url = clean_url(body.url)
    page = pg_client.get_page(url=url)

    if page:
        return AlreadyAdded(url=url)

    crawl_result = await crawl_only(Link.from_url(url))

    if crawl_result is None:
        raise HTTPException(400, "Could not crawl URL")

    return ShouldAdd(url=url)


class Crawl(BaseModel):
    title: str
    url: str
    excerpt: str
    type: str = "crawl"


@app.post('/crawl')
async def crawl_user(body: UrlRequest) -> Crawl | AlreadyAdded:
    url = clean_url(body.url)

    if pg_client.get_page(url=url) is not None:
        return AlreadyAdded(url=url)

    try:
        _, crawl_result = await crawl_interactive(Link.from_url(url))
        if crawl_result is None:
            raise HTTPException(400, "Could not crawl URL")

        return Crawl(
            excerpt=crawl_result.content[:1000],
            title=crawl_result.title,
            url=url)
    except Exception as e:
        print(e)
        raise HTTPException(400, "Could not crawl URL")


class CreatePageRequest(BaseModel):
    url: str
    userid: str


async def _create_page(body: CreatePageRequest) -> Page:
    link = Link(parent_url=f"user: {body.userid}", url=body.url, text="")
    vec, response = await crawl_interactive(link)
    page_response = pg_client.store_raw_page(3, response)

    if page_response is not None:
        await store_embeddings_for_pages([page_response])
    return page_response


@app.post('/add_page')
async def create_page(body: CreatePageRequest) -> PageResponse:
    existing_page = pg_client.get_page(url=body.url)
    if existing_page:
        return PageResponse.from_prisma_page(existing_page)

    page_response = await _create_page(body)

    if page_response is None:
        raise HTTPException(400, "Could not add page")

    return PageResponse.from_prisma_page(page_response)


@app.post('/message')
async def send_message(body: SendMessageRequest) -> None:
    """
    Send a message to another user
    :param body:
    :return:
    """

    # check if the message was already sent
    existing_message = await client.message.find_first(where={
        'sender_id': body.senderId,
        'receiver_id': body.receiverId,
        'page_id': body.pageId,
    })

    if existing_message:
        return

    await client.message.create(
        data={
            'message': body.message,
            'page_id': body.pageId,
            'receiver_id': str(body.receiverId),
            'sender_id': str(body.senderId),
            'url': body.url,
        }
    )


class GroupedMessage(BaseModel):
    message_ids: list[int]
    senders: list[Sender]
    page: PageResponse

    messages: list[Optional[str]]
    sent_on: list[datetime]

    @classmethod
    def from_messages(cls, messages: list[Message], page: PageResponse):
        return GroupedMessage(
            message_ids=[m.id for m in messages],
            senders=[Sender.from_message(m) for m in messages],
            page=page,
            messages=[m.message for m in messages],
            sent_on=[m.sent_on for m in messages]
        )


class UserFeedResponse(BaseModel):
    random_feed: list[PageResponse]
    messages: list[PageResponse]

# def group_page_responses(messages: list[PageResponse]) -> PageResponse:


@app.get('/global_feed')
async def get_global_feed() -> UserFeedResponse:
    messages = await client.message.find_many(order={'sent_on': 'desc'}, include={'sender': True, 'receiver': True}, where={
        'receiver_id': '4ee604f3-987d-4295-a2fa-b58d88e5b5e0'
    })

    result, pages = await _process_messages(messages)

    random_articles = await random_feed(limit=60)

    # Filter out stuff that alrdseady appears in the messages
    random_articles = [x for x in random_articles if x.id not in pages]

    return UserFeedResponse(random_feed=random_articles, messages=result)


# TODO: clean up and rename


@pytest.mark.asyncio
async def test_get_user_feed():
    await startup()
    result = await get_user_feed()

    print(result.json())


class UserQueryResponse(BaseModel):
    id: str
    firstName: str
    lastName: str
    profilePictureUrl: Optional[str]

    @classmethod
    def from_prisma(cls, pmodel: User):
        return UserQueryResponse(id=pmodel.id, firstName=pmodel.first_name, lastName=pmodel.last_name, profilePictureUrl=pmodel.profile_picture_url)


class CreateUserRequest(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    profileUrl: Optional[str]


@app.post('/create_user', status_code=201)
async def create_user(body: CreateUserRequest):
    """
    Create a new user
    :param body:
    :return:
    """

    res = await client.user.create({
        'id': body.id,
        'email': body.email,
        'first_name': body.firstName,
        'last_name': body.lastName,
        'profile_picture_url': body.profileUrl
    })
    return res


@app.get('/user/{user_uuid}')
async def get_user(user_uuid: str):
    """
    Get a user by their UUID
    :param user_uuid:
    :return:
    """

    if not user_uuid:
        raise HTTPException(400, "User ID must be provided")

    user = await client.user.find_first(where={'id': user_uuid})

    if user is None:
        return None
    return user


@app.get('/users')
async def get_search_users(query: str) -> list[UserQueryResponse]:
    """
    Substring search users by their query
    :param query:
    :return:
    """

    # LIMIT search results to <= 15
    # TODO: fix hardcoding of superstack gmail lol-  we don't use it bc it's for global broadcasts

    if not query:
        users = await client.query_raw("""
        WITH users_full_name AS (SELECT CONCAT(first_name, ' ', last_name) AS full_name, "User".* FROM "User")
                                       
        SELECT * from users_full_name AS uf 
        WHERE id != '4ee604f3-987d-4295-a2fa-b58d88e5b5e0' 
        ORDER BY created_at DESC LIMIT 15;""", model=User)
        # Sort based on prefix match

        return [UserQueryResponse.from_prisma(u) for u in users]

    sql_query = """
    WITH users_full_name AS (SELECT CONCAT(first_name, ' ', last_name) AS full_name, "User".* FROM "User")

    SELECT * from users_full_name AS uf WHERE uf.full_name ILIKE $1 
    AND id != '4ee604f3-987d-4295-a2fa-b58d88e5b5e0' LIMIT 15;"""
    users = await client.query_raw(sql_query, f'%{query}%', model=User)

    # TODO: Search by matching prefix first
    results = [UserQueryResponse.from_prisma(u) for u in users]

    return results


@pytest.mark.asyncio
async def test_search():
    await startup()
    results = await search(SearchQuery(query='climate'))
    print([x for x in results])


@pytest.mark.asyncio
async def test_like():
    await startup()

    await like(1, 14)


@app.post("/page")
async def find_page(body: FindPageRequest) -> Union[FindPageResponse, ShouldAdd]:
    url = clean_url(body.url)
    user_id = body.userId
    page = pg_client.get_page(url=url)

    if page is None:
        return ShouldAdd(url=url)

    pageres = PageResponse.from_prisma_page(page, dont_trim=True)

    pageres.senders = (await get_senders_for_pages(client, [page.id]))[page.id]

    if user_id:
        # a user has broadcasted if they are a sender and SPECIFICALLY they sent to the global broadcast special user
        has_broadcasted = any(
            [s.id == user_id and s.receiver_id == '4ee604f3-987d-4295-a2fa-b58d88e5b5e0' for s in pageres.senders])

    else:
        has_broadcasted = False

    comments, num_comments = await _create_comment_tree(page)
    return FindPageResponse(page=pageres, has_broadcasted=has_broadcasted, comments=comments, num_comments=num_comments, outbound_urls=page.outbound_urls)


async def _create_comment_tree(page: Page):
    # Get all comments that belong to this page
    comments = await client.comment.find_many(
        where={'page_id': page.id},
        include={
            'author': True,
        },
        order={'created_at': 'asc'}
    )
    num_comments = len(comments)

    # Create a dict with id -> comment
    comments_by_id = {c.id: c for c in comments}

    # Create a dict with parent_id -> list of comments
    children_by_parent: dict[int | None, list[Comment]] = defaultdict(list)
    for c in comments:
        children_by_parent[c.parent_id].append(c)

    # For each parent, populate the children list
    for parent_id, children in children_by_parent.items():
        if parent_id is None:
            continue

        parent = comments_by_id[parent_id]
        parent.children = children  # mutating

    # Sort only the root comments by updated_at (newest first)
    comments.sort(key=lambda x: x.updated_at, reverse=True)

    return [CommentResponse.from_comment(c) for c in comments if c.parent_id is None], num_comments


class FollowUserRequest(BaseModel):
    followerId: str
    followeeId: str


@app.post("/follow_user")
async def follow_user(body: FollowUserRequest) -> None:
    await client.user.update(
        where={
            'id': body.followerId
        },
        data={
            'following': {
                'connect': [{'id': body.followeeId}]
            }
        })


@app.post("/unfollow_user")
async def unfollow_user(body: FollowUserRequest) -> None:
    await client.user.update(
        where={
            'id': body.followerId
        },
        data={
            'following': {
                'disconnect': [{'id': body.followeeId}]
            }
        })


class UpdateUserRequest(BaseModel):
    id: str
    firstName: str
    lastName: str
    profileUrl: Optional[str]
    website: Optional[str]
    twitter: Optional[str]


@app.post('/update_user')
async def update_user(body: UpdateUserRequest) -> None:
    await client.user.update(
        where={
            'id': body.id
        },
        data={
            'first_name': body.firstName,
            'last_name': body.lastName,
            'profile_picture_url': body.profileUrl,
            'website': body.website,
            'twitter': body.twitter,
        }
    )


@app.get('/feed')
async def get_user_feed(userId: Optional[UUID] = None) -> list[PageResponse]:
    response = await mix_feed(client, str(userId) if userId is not None else None)
    return response


class CommentCreate(BaseModel):
    content: str
    pageId: int
    parentId: Optional[int] = None
    userId: str


class CommentUpdate(BaseModel):
    content: str
    commentId: int


@app.post("/comments")
async def create_comment(body: CommentCreate):
    # Check if the page exists
    page = pg_client.get_page(id=body.pageId)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Create a new comment

    if not body.parentId:
        new_comment = await client.comment.create({
            'author': {
                'connect': {
                    'id': body.userId
                }
            },
            'content': body.content,
            'page_id': body.pageId,
        }, include={'author': True})

        return CommentResponse.from_comment(new_comment)

    new_comment = await client.comment.create({
        'author': {
            'connect': {
                'id': body.userId
            }
        },
        'content': body.content,
        'page_id': body.pageId,
        'parent': {
            'connect': {
                'id': body.parentId
            }
        }
    }, include={'author': True})
    return CommentResponse.from_comment(new_comment)


@app.put("/comments")
async def update_comment(body: CommentUpdate):
    existing_comment = await client.comment.find_first(where={"id": body.commentId})
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    updated_comment = await client.comment.update(where={
        'id': body.commentId
    }, data={
        'content': body.content
    })

    return updated_comment


@app.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int):
    existing_comment = await client.comment.find_first(where={"id": comment_id})
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # we don't actually delete, we follow reddit's convention
    # Delete the content and set the deleted field to true (to maintain threads)

    deleted_comment = await client.comment.update(where={
        'id': comment_id
    }, data={
        'content': '',
        'is_deleted': True
    })

    return deleted_comment


# export interface PageNode {
#   title: string;
#   url: string;
#   id: number;
#   outboundUrls: string[]; // outbound urls
# }

class PageNode(BaseModel):
    title: str
    url: str
    id: int
    outboundUrls: list[str]

    @classmethod
    def from_page(cls, page: Page):
        return PageNode(title=page.title, url=page.url, id=page.id, outboundUrls=page.outbound_urls)


class PageNodesResponse(BaseModel):
    node: PageNode
    neighbors: list[PageNode]  # outbound


@app.post("/pagenodes")
async def get_outbound_nodes(body: UrlRequest):
    page = pg_client.get_page(url=body.url)

    if page is None:
        raise HTTPException(400, "Page does not exist")

    outbound_pages = pg_client.get_pages_by_url(page.outbound_urls)
    inbound_pages = pg_client.reverse_find_pages_by_url(body.url)

    combined_pages = outbound_pages + inbound_pages

    # deduplicate outbound and inbound
    deduplicated_pages = list({p.id: p for p in combined_pages}.values())

    # remove self reference
    deduplicated_pages = [p for p in deduplicated_pages if p.id != page.id]

    node = PageNode.from_page(page)

    neighbors = [PageNode.from_page(p) for p in deduplicated_pages]
    return PageNodesResponse(neighbors=neighbors, node=node)


@app.get("/inbox/{user_id}")
async def get_inbox(user_id: UUID):
    messages = await get_inbox_messages(client, str(user_id))
    inbox: list[PageResponse] = await page_ids_to_page_response(client, [x.page_id for x in messages])

    return inbox
