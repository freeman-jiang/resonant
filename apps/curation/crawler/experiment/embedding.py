import asyncio
import pytest
from psycopg.rows import class_row, dict_row
import os
from typing import Iterator

import numpy as np
import psycopg
from sentence_transformers import SentenceTransformer

from crawler.experiment.lda import cluster_documents_with_bertopic, PageWithVec
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

        if len(windows) > 12:
            # Get first 7 and last 5 of windows
            windows = windows[0:7] + windows[-5:]
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
    cursor = db.cursor(row_factory=dict_row)
    similar = cursor.execute("""
    -- Get average of the first 7 vectors for the article we WANT
    
 WITH want AS (SELECT avg(vec) as vec, url FROM vecs."Embeddings" WHERE url = %(url)s AND index <= 7 GROUP BY url)
 SELECT distinct ON (e1.url) e1.url as url, e2.avg_dist as distance FROM vecs."Embeddings" e1 RIGHT JOIN
 -- See which other articles matches that "want" average 
 (SELECT AVG(e.vec <=> w.vec) as avg_dist, e.url from vecs."Embeddings" as e, want as w WHERE e.url != w.url GROUP BY e.url ORDER BY  avg_dist LIMIT %(limit)s) e2
 ON e1.url = e2.url
    """, dict(url=doc_url, limit=5)).fetchall()

    urls_to_add = [x["url"] for x in similar]

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
                    'id': liked.id
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
                'id': 2
            }
        }
    }, include={'page': True, 'user': True})
    await generate_feed_from_liked(lp)


async def lda_test():
    cursor = db.cursor(row_factory=class_row(PageWithVec))
    pages = cursor.execute("""WITH pages AS (SELECT * FROM "Page" LIMIT 700)
SELECT * FROM pages INNER JOIN "vecs"."Embeddings" ON pages.url = "vecs"."Embeddings".url WHERE index < 10 ORDER BY pages.url, index
""").fetchall()

    print(cluster_documents_with_bertopic(pages))

    return


async def generate_embeddings():
    await client.connect()
    # await lda_test()
    # return

    while True:
        pages = await client.page.find_many(take=40, where={
            'embeddings': {
                'none': {}
            }
        })

        if len(pages) == 0:
            print("ERR: No pages to process")
            return
        to_append = []
        print("Calculating embeddings for {} pages".format(len(pages)))
        for p in pages:
            data = model.generate_vecs(p)
            to_append.extend(data)

        query = """INSERT INTO vecs."Embeddings" ("url", "index", "vec") VALUES {}""".format(",".join(
            ["('{}', '{}', '{}')".format(x[0], x[1], x[2]) for x in to_append]))
        await client.execute_raw(query)


if __name__ == "__main__":
    asyncio.run(generate_embeddings())
