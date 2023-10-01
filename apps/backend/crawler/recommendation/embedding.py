import asyncio
import os
from typing import Iterator, Optional, Callable

import nltk
import numpy as np
import psycopg
from psycopg import sql

from api.page_response import PageResponse
from dotenv import load_dotenv
from prisma import Prisma, models
from prisma.models import Page
from psycopg.rows import dict_row
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from crawler.prismac import PostgresClient
from ..dbaccess import db

load_dotenv()

client = Prisma()

assert len(os.environ['DATABASE_URL_PG']) > 1, "DATABASE_URL not set"
assert len(os.environ['DATABASE_URL_SUPABASE']) > 1, "DATABASE_URL not set"


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
    text_query: Optional[str]

    # (Case 2) Search by URL similarity (article already exists in the DB)
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


def _query_fts(query: str) -> list[PageResponse]:
    """
    Query using full-text search for exact word matches

    FTS `score` is a number between 0 and 1, where 1 is a perfect match
    :param query:
    :return:
    """
    sql_query = sql.SQL("""SELECT "Page".*,
               ts_rank(
                   ts,
                   {query}
               ) AS score
        FROM "Page"
        WHERE ts @@ {query}
        ORDER BY score DESC""").format(query=sql.SQL("plainto_tsquery('english', {})").format(query))
    cursor = db.cursor(row_factory=dict_row)

    similar = cursor.execute(sql_query, ).fetchall()

    return [PageResponse.from_page_dict(x) for x in similar]


def normalize_scores(pages: list[PageResponse], func: Optional[Callable] = None):
    """
    Normalize scores to be between 1 and 2
    """
    if len(pages) == 0:
        return

    scores = [x.score for x in pages]
    min_score = min(scores)
    max_score = max(scores)

    for p in pages:
        p.score = (p.score - min_score) / (max_score - min_score)

        if func:
            p.score = func(p.score)
        else:
            p.score = p.score + 1


def _query_similar(query: NearestNeighboursQuery) -> list[PageResponse]:
    """
    Combine results from vector search + full-text search to generate the best matching documents for a query

    TODO: from the FTS documents, use their embeddings to get similar documents? -- another way to get high quality similar
    articles

    :param query:
    :return:
    """
    embedding_results = _query_similar_embeddings(query)

    if query.text_query:
        fts_results = _query_fts(query.text_query)
    else:
        fts_results = []

    # Normalize scores
    for p in fts_results:
        p.score = 2.5 * (p.score ** 1.5) + 1.5
    normalize_scores(embedding_results, lambda x: x ** 2 + 1)

    # Combine them by pageid
    fts_results_dict = {x.id: x for x in fts_results}
    embedding_results_dict = {x.id: x for x in embedding_results}

    joined_keys = set(fts_results_dict.keys()).union(
        embedding_results_dict.keys())

    combined: list[PageResponse] = []

    for page_id in joined_keys:
        fts: Optional[PageResponse] = fts_results_dict.get(page_id)
        embedding: Optional[PageResponse] = embedding_results_dict.get(page_id)

        actual_page = fts if fts else embedding

        score = 1
        if fts is not None:
            score *= fts.score
        if embedding is not None:
            score *= embedding.score

        actual_page.score = score
        combined.append(actual_page)

    combined.sort(key=lambda x: x.score, reverse=True)
    return combined


def _query_similar_embeddings(query: NearestNeighboursQuery) -> list[PageResponse]:
    cursor = db.cursor(row_factory=dict_row)

    want_cte, want_cte_dict = query.to_sql_expr()
    similar = cursor.execute(f"""
    -- Get average of the first X vectors for the article we WANT
WITH want AS ({want_cte}),
 matching_vecs AS (
        SELECT e.vec <=> w.vec as dist, e.url as url from vecs."Embeddings" as e, want as w 
            WHERE e.url != w.url AND e.index <= 4 AND e.url NOT LIKE '%%.superstack-web.vercel.app' 
            ORDER BY dist LIMIT 250
 ),
 domain_counts AS (SELECT COUNT(url) as num_matching_windows, AVG(dist) as dist, MIN(url) as url FROM matching_vecs GROUP BY url)
 select "Page".*,
 -- Scoring algorithm: (similarity * page_rank^0.5 * (amount of matching windows ^ 0.15))
 -- Higher is better
 COALESCE((1 - dist) * ("Page".page_rank ^ 0.50) * (domain_counts.num_matching_windows ^ 0.25), -1) as score
  
  from "Page" INNER JOIN domain_counts ON domain_counts.url = "Page".url  ORDER BY score DESC
    """, want_cte_dict).fetchall()

    similar_urls = [
        PageResponse.from_prisma_page(Page(**x), x['score']) for x in similar
    ]

    return similar_urls


async def generate_feed_from_page(url: str) -> list[PageResponse]:
    query = NearestNeighboursQuery(url=url)
    similar = _query_similar(query)
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


async def generate_embeddings(db: PostgresClient):
    while True:
        pages = db.cursor(Page).execute(
            'SELECT * FROM "Page" WHERE "Page".url NOT IN (SELECT url FROM vecs."Embeddings" GROUP BY "url") ORDER BY "Page".created_at DESC LIMIT 10').fetchall()

        if len(pages) == 0:
            print("ERR: No pages to process")
            return

        await store_embeddings_for_pages(pages)


if __name__ == "__main__":
    client = PostgresClient()
    client.connect()
    asyncio.run(generate_embeddings(client))
