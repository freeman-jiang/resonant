import asyncio
import os
from typing import Iterator, Optional

import nltk
import numpy as np
import psycopg

from api.page_response import PageResponse
from dotenv import load_dotenv
from prisma import Prisma, models
from prisma.models import Page
from psycopg.rows import dict_row
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

load_dotenv()

client = Prisma()

assert len(os.environ['DATABASE_URL']) > 1, "DATABASE_URL not set"

db = psycopg.connect(os.environ['DATABASE_URL'])


def overlapping_windows(s: str, stride: int = 100, size: int = 120) -> Iterator[str]:
    arr: list[str] = nltk.word_tokenize(s)
    # Generate overlapping windows of arr as sentence-transformers token limit is 128
    for i in range(0, len(arr), stride):
        # i goes from 0, 0 + 100
        yield ' '.join(arr[i:i + size])


class Embedder:
    model: SentenceTransformer

    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2', device='cpu')

    def embed(self, text: str, stride: int = 100, size: int = 120) -> np.ndarray:
        """
        Sentence-transformers only supports small inputs, so we split the text into overlapping windows of X tokens each,
        and return the vectors for each window

        :param text:
        :return: ndarray of shape (n, 768) where n is the number of windows
        """
        windows = list(overlapping_windows(text, stride, size))
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


async def _query_similar(query: NearestNeighboursQuery) -> list[PageResponse]:
    cursor = db.cursor(row_factory=dict_row)

    want_cte, want_cte_dict = query.to_sql_expr()
    similar = cursor.execute(f"""
    -- Get average of the first X vectors for the article we WANT
WITH want AS ({want_cte}),
 matching_vecs AS (
        SELECT e.vec <=> w.vec as dist, e.url as url from vecs."Embeddings" as e, want as w 
            WHERE e.url != w.url AND e.index <= 4 AND e.url NOT LIKE '%%.superstack-web.vercel.app' 
            ORDER BY dist LIMIT 200
 ),
 domain_counts AS (SELECT COUNT(url) as num_matching_windows, AVG(dist) as dist, MIN(url) as url FROM matching_vecs GROUP BY url)
 select "Page".*,
 -- Scoring algorithm: (similarity * page_rank^0.5 * (amount of matching windows ^ 0.15))
 -- Higher is better
 (1 - dist) * ("Page".page_rank ^ 0.5) * (domain_counts.num_matching_windows ^ 0.15) as score
  
  from "Page" INNER JOIN domain_counts ON domain_counts.url = "Page".url ORDER BY score DESC
    """, want_cte_dict).fetchall()

    # Rerank based on number of matching windows + distance


    similar_urls = [
        PageResponse.from_prisma_page(Page(**x), x['score']) for x in similar
    ]

    return similar_urls


async def generate_feed_from_page(page: models.Page) -> list[PageResponse]:
    query = NearestNeighboursQuery(url=page.url or None)
    similar = await _query_similar(query)
    return similar


async def store_embeddings_for_pages(pages: list[Page]):
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

        await store_embeddings_for_pages( pages)


if __name__ == "__main__":
    asyncio.run(generate_embeddings())
