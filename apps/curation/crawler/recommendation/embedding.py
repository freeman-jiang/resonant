import asyncio
import os
from collections import defaultdict
from typing import Iterator, Optional

import nltk
import numpy as np
import psycopg
import pytest
from crawler.link import Link
from dotenv import load_dotenv
from prisma import Prisma, models
from prisma.models import Page
from psycopg.rows import class_row, dict_row
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

load_dotenv()

client = Prisma()
print(os.environ['DATABASE_URL'])
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
        """
        Sentence-transformers only supports small inputs, so we split the text into overlapping windows of X tokens each,
        and return the vectors for each window

        :param text:
        :return: ndarray of shape (n, 768) where n is the number of windows
        """
        windows = list(overlapping_windows(text))
        # Trim to first 7 windows only to save computation
        if len(windows) > 7:
            windows = windows[0:7]

        return self.model.encode(windows)

    def generate_vecs(self, title: str, content: str, url: str) -> list[tuple[str, int, list]]:
        """
        Get embedding for both the document text + title

        :return: List of tuples of (url, index, vec) where index is the index of the embedding in the document
        """

        model_input = title + " " + content
        embeddings = self.embed(model_input)
        to_append = []
        for idx, e in enumerate(embeddings):
            to_append.append(
                (
                    url,
                    idx,
                    e.tolist(),
                )
            )
        return to_append


model = Embedder()


class SimilarArticles(BaseModel):
    title: str
    url: str
    score: float

    def __hash__(self):
        return hash(self.url)

class NearestNeighboursQuery(BaseModel):
    vector: Optional[np.ndarray]
    url: Optional[str]

    class Config:
        arbitrary_types_allowed = True
    def __init__(self, **data):
        if 'vector' not in data and 'url' not in data:
            raise ValueError("Must provide either vector or url")
        super().__init__(**data)

    def to_sql_expr(self) -> tuple[str, dict]:
        if self.vector is not None:
            return f'SELECT CAST(%(vec)s as vector(768)) as vec, %(url)s as url', dict(vec=str(self.vector.tolist()), url=self.url or '')
        else:
            return 'SELECT avg(vec) as vec, url FROM vecs."Embeddings" WHERE url = %(url)s AND index <= 3 GROUP BY url', dict(url=self.url)

async def _query_similar(query: NearestNeighboursQuery) -> list[SimilarArticles]:
    cursor = db.cursor(row_factory=dict_row)

    want_cte, want_cte_dict = query.to_sql_expr()
    similar = cursor.execute(f"""
    -- Get average of the first X vectors for the article we WANT
WITH want AS ({want_cte}),
 matching_vecs AS (SELECT e.vec <=> w.vec as dist, e.url as url from vecs."Embeddings" as e, want as w WHERE e.url != w.url AND e.index <= 4 order by dist LIMIT 100),
 domain_counts AS (SELECT COUNT(url) as num_matching_windows, AVG(dist) as dist, MIN(url) as url FROM matching_vecs GROUP BY url)
 select "Page".*, domain_counts.dist, domain_counts.num_matching_windows from "Page" INNER JOIN domain_counts ON domain_counts.url = "Page".url ORDER BY dist
    """, want_cte_dict).fetchall()

    # Rerank based on number of matching windows + distance

    domain_counts = defaultdict(int)

    for idx, x in enumerate(similar):
        # Convert to higher score is better, simply based on the rank (e.g. first is highest)
        rank = len(similar) - idx

        domain = Link.from_url(x['url']).domain()
        domain_counts[domain] += 1

        if domain_counts[domain] >= 4:
            x['score'] = -1e10
            continue
        if domain_counts[domain] >= 1:
            rank -= 2 * (domain_counts[domain] ** 2) + 3

        # Boost based on how many matching windows the document has
        # The more matching windows, the more parts of the document are relevant
        x['score'] = rank + x['num_matching_windows']

    similar = sorted(similar, key=lambda x: x['score'], reverse=True)


    urls_to_add = [SimilarArticles(
        title=x['title'],
        url=x['url'],
        # Higher distance means lower similarity, so just negate it
        score=x['score']
    ) for x in similar]

    print("Found similar URLs to ", query, urls_to_add)

    return urls_to_add


async def generate_feed_from_liked(client: Prisma, lp: models.LikedPage):
    liked = lp.page
    query = NearestNeighboursQuery(url = liked.url or None)
    similar = await _query_similar(query)

    for article in similar:
        url = article.url
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
    return similar


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
                'id': 42
            }
        }
    }, include={'page': True, 'user': True})
    await generate_feed_from_liked(lp)


async def store_embeddings_for_pages(client: Prisma, pages: list[Page]):
    to_append = []
    print("Calculating embeddings for {} pages".format(len(pages)))
    for p in pages:
        data = model.generate_vecs(p.title, p.content, p.url)
        to_append.extend(data)

    cur = db.cursor()
    cur.executemany("""INSERT INTO vecs."Embeddings" ("url", "index", "vec") VALUES (%s, %s, %s)""", [
                    (x[0], x[1], x[2]) for x in to_append])
    db.commit()


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
