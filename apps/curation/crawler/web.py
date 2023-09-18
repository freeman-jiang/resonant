from collections import defaultdict
from datetime import datetime
from typing import Optional

import pytest
from crawler.worker import crawl_interactive
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nltk import sent_tokenize
from prisma import Prisma
from prisma.models import Page
from pydantic import BaseModel, validator

from .link import Link
from .recommendation.embedding import (NearestNeighboursQuery, SimilarArticles,
                                       _query_similar,
                                       generate_feed_from_liked, model)
from .worker import get_window_avg

app = FastAPI()
client = Prisma()

app = FastAPI()

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
    await client.connect()


async def find_or_create_user(userid):
    # Check if the user exists
    existing_user = await client.user.find_first(where={"id": userid})

    if existing_user:
        # User already exists
        return existing_user

    # If the user doesn't exist, create a new user
    new_user = await client.user.create(
        data={
            # Add other user properties as needed
        }
    )

    return new_user


@app.get("/like/{userid}/{pageid}")
async def like(userid: int, pageid: int) -> list[SimilarArticles]:
    page = await client.page.find_first(where={"id": pageid})
    user = await find_or_create_user(userid)

    lp = await client.likedpage.find_first(where={
        'user_id': user.id,
        'page_id': page.id,
    }, include={'page': True, 'user': True, 'suggestions': {
        'include': {'page': True}
    }})
    if lp:
        suggestions = lp.suggestions

        urls = []

        for s in suggestions:
            urls.append(SimilarArticles(title=s.page.title,
                                        url=s.page.url, score=s.score))
    else:
        lp = await client.likedpage.create(data={
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
        urls = await generate_feed_from_liked(client, lp)

    print("Recommended", urls)
    return urls


class PageResponse(BaseModel):
    id: int
    url: str
    title: str
    excerpt: str
    date: str = ""

    @classmethod
    def from_prisma_page(cls, p: Page) -> 'PageResponse':
        # Get first two sentences from p.content
        excerpt = sent_tokenize(p.content)[:2]

        return PageResponse(
            id=p.id,
            url=p.url,
            title=p.title,
            date=p.date or "",
            excerpt='. '.join(excerpt)
        )


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
async def search(body: SearchQuery) -> list[SimilarArticles]:
    if body.url:
        url = body.url
        print("Searching for similar URLs to", url)

        want_vec = await crawl_interactive(Link.from_url(url))

        query = NearestNeighboursQuery(vector=want_vec, url=url)
        similar = await _query_similar(query)

        return similar
    else:
        want_vec = get_window_avg(body.query)
        query = NearestNeighboursQuery(vector=want_vec)
        similar = await _query_similar(query)
        return similar


def test_search():
    import asyncio
    asyncio.run(search(
        'https://www.theguardian.com/lifeandstyle/2017/aug/11/why-we-fell-for-clean-eating'))


@pytest.mark.asyncio
async def test_like():
    await startup()

    await like(1, 5330)


@app.get("/topic/{topic}")
async def get_topic(topic: str) -> list[PageResponse]:
    topic_url = f'https://{topic}.topics.superstack-web.vercel.app'
    query = NearestNeighboursQuery(url=topic_url)

    suggestions = await _query_similar(query)
    url_list = [s.url for s in suggestions]

    pages = await client.page.find_many(where={
        'url': {
            'in': url_list
        }
    })

    return [PageResponse.from_prisma_page(p) for p in pages]


@pytest.mark.asyncio
async def test_get_topic():
    await startup()

    print(await get_topic("philosophy"))


@app.get("/feed")
async def pages() -> list[PageResponse]:
    crawltasks = await client.crawltask.find_many(take=120, where={
        "depth": {
            'lt': 2
        },
        'status': 'COMPLETED'
    })

    # CONVERT the above to a raw query
    # crawltasks = await client.query_raw("""SELECT * FROM "CrawlTask" WHERE depth <= 1 AND status = 'COMPLETED' ORDER BY RANDOM() LIMIT 120""", model=CrawlTask)

    domain_count = defaultdict(int)

    pages_to_return = []
    for ct in crawltasks:
        page = await client.page.find_first(where={'url': ct.url})

        if page:
            domain = Link.from_url(page.url).domain()

            if domain == page.url.strip('/'):
                # Filter out home pages (they are not articles)
                continue

            domain_count[domain] += 1

            if domain_count[domain] > 3:
                continue

            pages_to_return.append(PageResponse.from_prisma_page(page))
    return pages_to_return


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

    random_pages = await client.query_raw("""
    WITH random_ids AS (SELECT id, MD5(CONCAT($1, content_hash)) FROM "Page" ORDER BY md5)
    SELECT p.* From "Page" p INNER JOIN random_ids ON random_ids.id = p.id WHERE p.depth <= 1 LIMIT $2
    """, seed, 10, model=Page)

    return [PageResponse.from_prisma_page(p) for p in random_pages]


@pytest.mark.asyncio
async def test_random_feed():
    await startup()

    print(await random_feed())

if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", '8000'))

    uvicorn.run(app, host=host, port=port)
