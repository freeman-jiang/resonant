import os
import random
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

import pytest
from api.page_response import PageResponse, PageResponseURLOnly
from crawler.link import Link
from crawler.prismac import PostgresClient
from crawler.recommendation.embedding import (NearestNeighboursQuery,
                                              _query_similar,
                                              generate_feed_from_page, store_embeddings_for_pages)
from crawler.worker import crawl_interactive, get_window_avg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
from prisma.models import Message, Page, User
from pydantic import BaseModel, validator

load_dotenv()

app = FastAPI()
client = Prisma(datasource={'url': os.environ['DATABASE_URL_SUPABASE']})
db = PostgresClient(None)

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
    db.connect()


async def find_user(userid: str):
    # Check if the user exists
    existing_user = await client.user.find_first(where={"id": userid})

    if existing_user:
        # User already exists
        return existing_user


class LinkQuery(BaseModel):
    url: str

    @validator("url")
    def check_url(cls, v: str):
        Link.from_url(v)
        return v


@app.post("/page")
async def link(body: LinkQuery) -> Optional[PageResponse]:
    url = body.url
    page = db.get_page(url=url)

    if page is None:
        return None
    return PageResponse.from_prisma_page(page)


@app.get('/recommend')
async def recommend(userid: int) -> list[PageResponse]:
    """
    Get a random sample of similar pages from the pages user has already liked from LikedPage
    :param userid:
    :return:
    """

    user = await find_user(userid)

    # Get a random sample of pages the user has liked
    liked_pages = await client.likedpage.find_many(take=100, where={
        'user_id': user.id
    }, include={'page': True})

    # Select K random pages to generate feed from
    selected_liked_pages = random.choices(
        liked_pages, k=min(10, len(liked_pages)))

    if len(selected_liked_pages) == 0:
        print(f'User {userid} has no liked pages')
        return []

    similar = []

    for lp in selected_liked_pages:
        page = lp.page
        similar.extend(await generate_feed_from_page(page.url))

    return similar


@app.get('/saved/{userid}')
async def get_liked_pages(userid: str) -> list[PageResponse]:
    lps = await client.likedpage.find_many(take=100, where={
        'user_id': userid,
    })

    # sort by most recent
    lps.sort(key=lambda x: x.created_at, reverse=True)
    page_ids = [lp.page_id for lp in lps]

    pages = db.get_pages_by_id(page_ids)
    # sort by most recent
    pages.sort(key=lambda x: page_ids.index(x.id))

    return [PageResponse.from_prisma_page(p) for p in pages]


@app.get("/like/{userid}/{pageid}")
async def like(userid: str, pageid: int) -> None:
    page = db.get_page(id=pageid)

    if page is None:
        raise HTTPException(400, "Page does not exist")

    user = await find_user(userid)
    if not user:
        raise HTTPException(400, "User does not exist")

    await upsert_liked_page(page, user)
    # urls = await generate_feed_from_page(page.url)

    # print("Recommended", urls)
    return None


async def upsert_message(user: User, page: Page):
    message = await client.message.find_first(where={
        'page_id': page.id,
        'sender_id': user.id,
    })
    if message is None:
        await client.message.create(data={
            'page_id': page.id,
            'sender_id': user.id,
            # Hardcode superstack.app@gmail.com ID for global shares
            'receiver_id': '4ee604f3-987d-4295-a2fa-b58d88e5b5e0',
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


@app.post("/search")
async def search(body: SearchQuery) -> list[PageResponse]:
    if body.url:
        url = body.url
        print("Searching for similar URLs to", url)

        contains_url = db.query(
            'SELECT 1 FROM "Page" p INNER JOIN Embeddings e ON p.url = e.url WHERE p.url = %s', [url])

        if contains_url:
            print("Found existing URL!")
            query = NearestNeighboursQuery(url=url)
        else:
            print("Crawling this URL")
            want_vec, _ = await crawl_interactive(Link.from_url(url))
            query = NearestNeighboursQuery(vector=want_vec, url=url)

        similar = _query_similar(query)

        return similar
    else:
        want_vec = get_window_avg(body.query)
        query = NearestNeighboursQuery(vector=want_vec, text_query=body.query)
        similar = _query_similar(query)
        return similar


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/random-feed")
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

    random_pages = db.query("""
    WITH random_ids AS (SELECT id, MD5(CONCAT(%s::text, content_hash)) FROM "Page" ORDER BY md5)
    SELECT p.* From "Page" p INNER JOIN random_ids ON random_ids.id = p.id WHERE p.depth <= 1 LIMIT %s
    """, [seed, limit])

    random_pages = [Page(**p) for p in random_pages]
    return [PageResponse.from_prisma_page(p) for p in random_pages]


@app.post('/share/{user_id}/{page_id}')
async def share_page(user_id: str, page_id: int) -> None:
    page = db.get_page(id=page_id)

    if page is None:
        raise HTTPException(400, "Page does not exist")

    user = await find_user(user_id)
    if not user:
        raise HTTPException(400, "User does not exist")

    await upsert_message(user, page)
    return None


class SendMessageRequest(BaseModel):
    sender_id: UUID
    page_id: Optional[int]
    url: Optional[str]
    message: str
    receiver_id: UUID

    def __init__(self, **data):
        assert 'url' in data or 'page_id' in data, "URL or page_id must be provided"
        super().__init__(**data)

    @validator("sender_id", "receiver_id", pre=False)
    def validate_uuids(cls, value):
        """
        Converts the UUIDs to a string when we call the .dict() method
        :param value:
        :return:
        """
        if value:
            return str(value)
        return value

class CreatePageRequest(BaseModel):
    url: str


async def _create_page(body: CreatePageRequest) -> Page:
    vec, response = await crawl_interactive(Link.from_url(body.url))
    page_response = db.store_raw_page(3, response)

    await store_embeddings_for_pages([page_response])
    return page_response

@app.post('/page')
async def create_page(body: CreatePageRequest) -> PageResponse:
    page_response = await _create_page(body)
    return PageResponse.from_prisma_page(page_response)


@pytest.mark.asyncio
async def test_create_page():
    db.connect()
    await create_page(CreatePageRequest(url = 'https://student.cs.uwaterloo.ca/~cs241e/current/a3.html'))

@app.post('/message')
async def send_message(body: SendMessageRequest) -> None:
    """
    Send a message to another user
    :param body:
    :return:
    """

    if body.url is not None:
        # Check if the URL doesn't exist in our database. If not, then crawl it
        page = db.get_page(url=body.url)
        if page is None:
            page = await _create_page(CreatePageRequest(url=body.url))
            body.page_id = page.id
            body.url = None

    message = body.dict()

    await client.message.create(message)


@pytest.mark.asyncio
async def test_send_message():
    await startup()
    await send_message(SendMessageRequest(
        sender_id='61b98b24-18ff-43eb-af97-c58cd386e748',
        page_id = None,
        url='https://www.nytimes.com/2023/10/04/us/politics/house-speaker-mccarthy.html',
        message='fdas',
        receiver_id='083e93f0-2fd9-4454-ad46-3444378f4b51'
    ))


class MessageUser(BaseModel):
    id: UUID
    first_name: str
    last_name: str


class MessageResponse(BaseModel):
    page: Union[PageResponse, PageResponseURLOnly]
    sender: MessageUser
    receiver: MessageUser

    message: str


class UserFeedResponse(BaseModel):
    random_feed: list[PageResponse]
    messages: list[MessageResponse]


@app.get('/feed')
async def get_user_feed(userid: UUID) -> UserFeedResponse:
    """
    Get the user's feed by combining their incoming messages and stuff from random-feed
    :param userid:
    :return:
    """

    messages = await client.message.find_many(where={'receiver_id': str(userid)}, order={'sent_on': 'desc'}, include={'sender': True, 'receiver': True})

    page_ids_to_fetch = set(
        [m.page_id for m in messages if m.page_id is not None])

    pages = db.get_pages_by_id(list(page_ids_to_fetch))

    pages = {p.id: p for p in pages}

    result = []

    for r in messages:
        if r.page_id is not None:
            page = pages[r.page_id]
            page_response = PageResponse.from_prisma_page(page)
        else:
            page_response = PageResponseURLOnly(url=r.url)

        result.append(MessageResponse(
            page=page_response,
            sender=MessageUser(
                id=r.sender_id, first_name=r.sender.first_name, last_name=r.sender.last_name),
            receiver=MessageUser(
                id=r.receiver_id, first_name=r.receiver.first_name, last_name=r.receiver.last_name),
            message=r.message
        ))

    random_articles = await random_feed(limit=30)

    return UserFeedResponse(random_feed=random_articles, messages=result)


@pytest.mark.asyncio
async def test_get_user_feed():
    await startup()
    result = await get_user_feed('083e93f0-2fd9-4454-ad46-3444378f4b51')
    print(result)


class UserQueryResponse(BaseModel):
    user_id: UUID
    fname: str
    lname: str

    @classmethod
    def from_prisma(cls, pmodel: User):
        return UserQueryResponse(user_id=pmodel.id, fname=pmodel.first_name, lname=pmodel.last_name)


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

    sql_query = """WITH users_full_name AS (SELECT CONCAT(first_name, ' ', last_name) AS full_name, "User".* FROM "User")
        select * from users_full_name uf where uf.full_name ILIKE $1;"""
    users = await client.query_raw(sql_query, f'%{query}%', model=User)

    return [UserQueryResponse.from_prisma(u) for u in users]


@pytest.mark.asyncio
async def test_random_feed():
    await startup()

    print(await random_feed())


@pytest.mark.asyncio
async def test_search():
    await startup()
    results = await search(SearchQuery(url='http://www.naughtycomputer.uk/owned_software_servant_software.html'))
    print([x.url for x in results])


@pytest.mark.asyncio
async def test_like():
    await startup()

    await like(1, 14)
