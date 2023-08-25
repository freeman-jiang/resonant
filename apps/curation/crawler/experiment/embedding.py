import asyncio
import os

import numpy as np
import vecs
from sentence_transformers import SentenceTransformer

from crawler.link import Link
from crawler.parse import CrawlResult
from dotenv import load_dotenv
from prisma import Prisma
from prisma.models import Page

load_dotenv()

client = Prisma()

class Embedder:
    model: SentenceTransformer
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')

    def embed(self, text: str) -> np.ndarray:
        return self.model.encode(text)

model = SentenceTransformer('all-mpnet-base-v2')
vx = vecs.create_client(os.environ['DATABASE_URL'])

embeddings = vx.get_or_create_collection(name="embeddings", dimension=384)


def create_index():
    embeddings.create_index(measure=vecs.IndexMeasure.cosine_distance)


def generate_embedding_for_document(document: Page):
    """
    Get embedding for both the document text + title

    :param document:
    :return:
    """

    model_input = document.title + " " + document.content
    embedding = model.encode(model_input)
    return embedding



def query_similar(doc_url: str):
    document, embedding, metadata = embeddings.fetch([doc_url])[0]
    similar = embeddings.query(
        data=embedding,  # required
        limit=5,  # number of records to return
        filters={},  # metadata filters
        measure="cosine_distance",  # distance measure to use
        include_value=True,  # should distance measure values be returned?
        include_metadata=False,  # should record metadata be returned?
    )

    for simurl, distance in similar:
        print("Most similar to ", doc_url, "is:", simurl, distance, metadata)


async def query_similar_test():
    pages = await client.page.find_many(take = 100, where = {
        'embeddings': {
            'isNot': None
        }
    })
    print(pages)

    for p in pages:
        query_similar(p.url)

    return

async def main():
    cr = CrawlResult(
        link=Link.from_url("https://taoofmac.com/space/blog/2023/08/20/1600"),
        title="SUMMER MINIMALISM",
        date="2021-01-04T10:00:00-05:00",
        author="HENRY TESTING",
        content="""
SUMMER MINIMALISM

As the haziness of mid-summer starts to fade away, I am starting to worry a bit more about my interminable personal backlog and getting back to some unfinished projects. 
But not just yet. Amidst a series of (perhaps merciful) failures tinkering with generative AI (I’m still quite unhappy with the quality of LLM libraries and overall tooling, let alone the models’ inability to yield useful replies even with retrieval augmented generation and other prompt enrichment approaches), I decided to spend some free time on the minimalist side of computing again.

It happens every Summer, I guess. hacking e-readers, revisiting Plan9, building pocket travel servers, stuffing LISP into them, and, last year, going thin client.

This year, besides a dive into minimalist keyboards (which, incidentally, is going well enough to type this) I’m again struck with the notion of finding a “minimal stack” to both do quick prototyping and “high performance” services in smaller chips (like low-end ARM CPUs), so I’ve been poking at things like Rampart, Mako and a couple of C++ frameworks.

This would ordinarily be the space I created piku for, except that I’m considering going a bit lower in specs than a modern Raspberry Pi. This means either a stable, zero-hype low-level language or an embeddable scripting one.

But looking back, piku actually came out of a similar exercise, except that one of the design goals was to re-use as much of the typical Linux package ecosystem as possible.

Right now my checklist looks like this:

Good HTTP (client and server), JSON and SQLite support (i.e., enough “batteries included” to be able to do a lot of things without having to pull in dependencies).
Some form of Markdown support (because I want it to be self-documenting).
Low memory footprint.
Good support for parallelism and concurrency, especially concerning networking.
But since I am doing this for fun, I am again going off the beaten path. I grabbed a bunch of LISP and Scheme related stuff1, ran some of it through Sigil and sent the resulting EPUB files to my Kindle to read while on the beach (or, more euphemistically given the current climate, “the ultimate silicon grill”).

I am tempted to use Janet and uLisp, but that might be a tad extreme so I’m focusing on Guile Scheme to begin with since it has been around forever. ↩︎
        """,
        outgoing_links=[]
    )

    await client.connect()

    # await query_similar_test()
    # return

    pages = await client.page.find_many(take = 500, where = {
        'embeddings': {
            'is': None
        }
    })

    if len(pages) == 0:
        print("ERR: No pages to process")
        return
    to_append = []
    for p in pages:
        print(p.url)
        embedding = generate_embedding_for_document(p)
        to_append.append(
                (
                    p.url,
                    embedding,
                    {}
                )
        )
    embeddings.upsert(
        records=to_append
    )


if __name__ == "__main__":
    print(model.encode(['this is a sentence', 'and this is another sentence']))
    asyncio.run(main())
