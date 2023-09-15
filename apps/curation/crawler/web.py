from collections import defaultdict
from nltk import sent_tokenize
from prisma.models import Page

from fastapi import FastAPI
from pydantic import BaseModel

from link import Link
from prisma import Prisma
from recommendation.embedding import generate_feed_from_liked
app = FastAPI()
client = Prisma()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
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
async def like(userid: int, pageid: int):
    page = await client.page.find_first(where={"id": pageid})
    user = await find_or_create_user(userid)
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
    return urls

def sentences(text: str) -> list[str]:
    return sent_tokenize(input_string)
class PageResponse(BaseModel):
    id: int
    url: str
    title: str
    date: str
    excerpt: str


    @classmethod
    def from_prisma_page(cls, p: Page) -> 'PageResponse':
        # Get first two sentences from p.content
        excerpt = sent_tokenize(p.content)[:2]

        return PageResponse(
            id = p.id,
            url = p.url,
            title = p.title,
            date = p.date,
            excerpt='. '.join(excerpt)
        )

@app.get("/pages")
async def pages() -> list[PageResponse]:
    crawltasks = await client.crawltask.find_many(take = 120, where = {
        "depth": {
            'lt': 2
        },
        'status': 'COMPLETED'
    })

    domain_count = defaultdict(int)

    pages_to_return = []
    for ct in crawltasks:
        page = await client.page.find_first(where = {'url': ct.url})

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