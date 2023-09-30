import os
import random
from datetime import datetime
from typing import Optional

import pytest
from api.page_response import PageResponse
from crawler.link import Link
from crawler.prismac import PostgresClient
from crawler.recommendation.embedding import (NearestNeighboursQuery,
                                              _query_similar,
                                              generate_feed_from_page)
from crawler.worker import crawl_interactive, get_window_avg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
from prisma.models import Page, User
from pydantic import BaseModel, validator

load_dotenv()

app = FastAPI()
client = Prisma(datasource={'url': os.environ['DATABASE_URL_SUPABASE']})
db = PostgresClient(None)

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://app-superstack.vercel.app"
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


async def find_or_create_user(userid):
    # Check if the user exists
    existing_user = await client.user.find_first(where={"id": userid})

    if existing_user:
        # User already exists
        return existing_user

    # If the user doesn't exist, create a new user
    new_user = await client.user.create(
        data={
            "id": userid
        }
    )

    return new_user


class LinkQuery(BaseModel):
    url: str

    @validator("url")
    def check_url(cls, v: str):
        Link.from_url(v)
        return v


@app.post("/page")
async def link(body: LinkQuery) -> PageResponse:
    url = body.url
    page = db.get_page(url = url)
    return PageResponse.from_prisma_page(page)


@app.get('/recommend')
async def recommend(userid: int) -> list[PageResponse]:
    """
    Get a random sample of similar pages from the pages user has already liked from LikedPage
    :param userid:
    :return:
    """

    user = await find_or_create_user(userid)

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


@app.get("/like/{userid}/{pageid}")
async def like(userid: int, pageid: int) -> list[PageResponse]:
    page = db.get_page(id = pageid)

    if page is None:
        raise HTTPException(400, "Page does not exist")

    user = await find_or_create_user(userid)

    await upsert_liked_page(page, user)
    urls = await generate_feed_from_page(page.url)

    print("Recommended", urls)
    return urls


async def upsert_liked_page(page: Page, user: User):
    """
    Upserts a LikedPage for the given user and page
    :param page:
    :param user:
    :return:
    """
    lp = await client.likedpage.find_first(where={
        'user_id': user.id,
        'page_id': page.id,
    }, include={'page': True, 'user': True, 'suggestions': {
        'include': {'page': True}
    }})
    if lp is None:
        await client.likedpage.create(data={
            'user': {
                'connect': {
                    'id': user.id
                }
            },
            'page': {
                'connect': {
                    'id': page.id
                }
            }
        }, include={'page': True, 'user': True})


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

        contains_url = db.query("SELECT 1 FROM \"Page\" WHERE url = %s", [url])

        if contains_url:
            print("Found existing URL!")
            query = NearestNeighboursQuery(url=url)
        else:
            print("Crawling this URL")
            want_vec = await crawl_interactive(Link.from_url(url))
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
async def random_feed() -> list[PageResponse]:
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
    seed = current_datetime.strftime("%Y-%m-%d")

    random_pages = db.query("""
    WITH random_ids AS (SELECT id, MD5(CONCAT(%s::text, content_hash)) FROM "Page" ORDER BY md5)
    SELECT p.* From "Page" p INNER JOIN random_ids ON random_ids.id = p.id WHERE p.depth <= 1 LIMIT %s
    """, [seed, 100])

    random_pages = [Page(**p) for p in random_pages]
    return [PageResponse.from_prisma_page(p) for p in random_pages]


@pytest.mark.asyncio
async def test_random_feed():
    await startup()

    print(await random_feed())


@pytest.mark.asyncio
async def test_search():
    await startup()
    results = await search(SearchQuery(url='http://dieordiy2.blogspot.com/2023/09/melvins-tribute-to-kinks-amphetamine.html'))
    print([x.url for x in results])


@pytest.mark.asyncio
async def test_like():
    await startup()

    await like(1, 14)
