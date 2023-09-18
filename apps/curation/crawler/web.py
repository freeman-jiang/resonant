from collections import defaultdict
import pytest

from crawler.worker import crawl_interactive
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nltk import sent_tokenize
from prisma import Prisma
from prisma.models import CrawlTask, Page
from pydantic import BaseModel

from .link import Link
from .recommendation.embedding import (NearestNeighboursQuery, SimilarArticles,
                                       _query_similar,
                                       generate_feed_from_liked)

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


@app.get("/search/{url:path}")
async def search(url: str) -> list[SimilarArticles]:
    print("Searching for similar URLs to", url)

    want_vec = await crawl_interactive(Link.from_url(url))

    query = NearestNeighboursQuery(vector=want_vec, url=url)
    similar = await _query_similar(query)

    print("Similar articles to", url, similar)
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


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", '8000'))

    uvicorn.run(app, host=host, port=port)
