import asyncio
import pytest
from psycopg.rows import class_row
import os
from typing import Iterator

import numpy as np
import psycopg
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv
from prisma import Prisma, models
from prisma.models import Page
import nltk

load_dotenv()

client = Prisma()
db = psycopg.connect(os.environ['DATABASE_URL'])


def overlapping_windows(s: str) -> Iterator[str]:
    arr: list[str] = nltk.word_tokenize(s)
    # Generate overlapping windows of arr as sentence-transformers token limit is 128
    for i in range(0, len(arr), 100):
        # i goes from 0, 0 + 100
        yield ' '.join(arr[i:i + 120])


class Embedder:
    model: SentenceTransformer

    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')

    def embed(self, text: str) -> np.ndarray:
        windows = list(overlapping_windows(text))
        # Trim to first 7 windows only to save computation
        if len(windows) > 7:
            windows = windows[0:7]

        return self.model.encode(windows)

    def generate_vecs(self, document: Page) -> list[tuple[str, int, list]]:
        """
        Get embedding for both the document text + title

        :param document:
        :return:
        """

        model_input = document.title + " " + document.content
        embeddings = self.embed(model_input)
        to_append = []
        for idx, e in enumerate(embeddings):
            to_append.append(
                (
                    document.url,
                    idx,
                    e.tolist(),
                )
            )
        return to_append


# model = SentenceTransformer('all-mpnet-base-v2')

model = Embedder()


async def _query_similar(doc_url: str) -> list[str]:
    cursor = db.cursor(row_factory=class_row(models.Embeddings))
    similar = cursor.execute("""
    -- Get average of the first X vectors for the article we WANT
 WITH want AS (SELECT avg(vec) as vec, url FROM vecs."Embeddings" WHERE url = %(url)s AND index <= 7 GROUP BY url)
 SELECT embed.* FROM vecs."Embeddings" as embed INNER JOIN
 (SELECT AVG(e.vec <=> w.vec) as avg_dist, e.url from vecs."Embeddings" as e, want as w WHERE e.url != w.url GROUP BY e.url ORDER BY  avg_dist LIMIT %(limit)s) matching_docs
 ON embed.url = matching_docs.url
    """, dict(url=doc_url, limit=50)).fetchall()

    urls_to_add = list(set(x.url for x in similar))

    return urls_to_add


async def generate_feed_from_liked(lp: models.LikedPage):
    liked = lp.page
    urls = await _query_similar(liked.url)
    for url in urls:
        await client.feedpage.create(data={
            'page': {
                'connect': {
                    'url': url
                }
            },
            'user': {
                'connect': {
                    'id': lp.user.id
                }
            },
            'suggested_from': {
                'connect': {
                    'id': lp.id
                }
            }
        })


@pytest.mark.asyncio
async def test_query_similar():
    await client.connect()
    user = await client.user.create(data={})
    lp = await client.likedpage.create(data={
        'user': {
            'connect': {
                'id': user.id
            }
        },
        'page': {
            'connect': {
                'id': 56
            }
        }
    }, include={'page': True, 'user': True})
    await generate_feed_from_liked(lp)


async def store_embeddings_for_pages(client: Prisma, pages: list[Page]):
    to_append = []
    print("Calculating embeddings for {} pages".format(len(pages)))
    for p in pages:
        data = model.generate_vecs(p)
        to_append.extend(data)

    query = """INSERT INTO vecs."Embeddings" ("url", "index", "vec") VALUES {}""".format(",".join(
        ["('{}', '{}', '{}')".format(x[0], x[1], x[2]) for x in to_append]))
    await client.execute_raw(query)


async def generate_embeddings():
    await client.connect()

    while True:
        pages = await client.page.find_many(take=10, where={
            'embeddings': {
                'none': {}
            },
            # 'url': {
            #     'endsWith': 'topics.superstack-web.vercel.app'
            # }
        })

        if len(pages) == 0:
            print("ERR: No pages to process")
            return

        await store_embeddings_for_pages(client, pages)


if __name__ == "__main__":
    asyncio.run(generate_embeddings())
