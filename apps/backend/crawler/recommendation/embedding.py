import asyncio
import os
from multiprocessing import freeze_support
from typing import Callable, Iterator, Optional

import nltk
import numpy as np
from api.page_response import PageResponse
from crawler.prismac import PostgresClient
from dotenv import load_dotenv
from prisma import Prisma, models
from prisma.models import Page
from psycopg import Cursor, sql
from psycopg.rows import dict_row
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from ..dbaccess import DB, db

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
        self.model = SentenceTransformer('BAAI/bge-base-en-v1.5')

    def embed(self, text: str, stride: int = 360, size: int = 380, for_query: bool = False) -> np.ndarray:
        """
        Sentence-transformers only supports small inputs, so we split the text into overlapping windows of X tokens each,
        and return the vectors for each window

        :param text:
        :return: ndarray of shape (n, 768) where n is the number of windows
        """

        windows = list(overlapping_windows(text, stride, size))

        if for_query:
            windows = [
                "Represent this sentence for searching relevant passages:" + x for x in windows]
        # Trim to first N windows only to save computation
        if len(windows) > 3:
            windows = windows[0:3]

        return self.encode(windows)

    def encode(self, windows):
        result = self.model.encode(windows, normalize_embeddings=True)
        print("Using device", self.model.device)

        return result

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

    def get_vector(self, cursor: Cursor):
        """
        Get the vector for the given URL so we can search for it
        It's insanely slow if we do it in the same query using a CTE because postgres optimizer
        """
        if self.vector is None:
            result = cursor.execute(
                'SELECT avg(vec) as vec, url FROM Embeddings WHERE url = %(url)s GROUP BY url', dict(url=self.url)).fetchall()
            self.vector = np.array(result[0]['vec'])

    def to_sql_expr(self) -> tuple[str, dict]:
        if self.vector is not None:
            return f'SELECT CAST(%(vec)s as vector(768)) as vec, %(url)s as url', dict(vec=str(self.vector.tolist()), url=self.url or '')
        else:
            raise RuntimeError(
                "Unreachable--should have called NearestNeighboursQuery.get_vector()")
            return 'SELECT avg(vec) as vec, url FROM Embeddings WHERE url = %(url)s GROUP BY url', dict(url=self.url)


def _query_fts(query: str) -> list[PageResponse]:
    """
    Query using full-text search for exact word matches

    FTS `score` is a number between 0 and 1, where 1 is a perfect match

    The rules for query are:
        unquoted text: text not inside quote marks will be converted to terms separated by & operators, as if processed by plainto_tsquery.
        "quoted text": text inside quote marks will be converted to terms separated by <-> operators, as if processed by phraseto_tsquery.
        OR: the word “or” will be converted to the | operator.
        -: a dash will be converted to the ! operator.
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
        ORDER BY score DESC LIMIT 50""").format(query=sql.SQL("websearch_to_tsquery('english', {})").format(query))
    cursor = db.cursor(row_factory=dict_row)

    similar = cursor.execute(sql_query, ).fetchall()

    return [PageResponse.from_page_dict(x) for x in similar]


def test_query_fts():
    print(_query_fts('"python language"'))


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
    # embedding_results = []

    # IGNORE FTS FOR NOW, takes too long
    if query.text_query and '"' in query.text_query:
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
    query.get_vector(cursor)

    want_cte, want_cte_dict = query.to_sql_expr()

    # if it's a text query, then vector search is more useless
    embedding_weight = 0.25 if query.text_query is not None else 1.0

    want_cte_dict['embedding_weight'] = embedding_weight
    similar = cursor.execute(f"""
    -- Get average of the first X vectors for the article we WANT
WITH want AS ({want_cte}),
 matching_vecs AS (
        SELECT e.vec <=> w.vec as dist, e.url as url from Embeddings as e, want as w 
            WHERE e.url != w.url
            ORDER BY dist LIMIT 250
 ),
 domain_counts AS (SELECT COUNT(url) as num_matching_windows, AVG(dist) as dist, MIN(url) as url FROM matching_vecs GROUP BY url)
 select "Page".*,
 -- Scoring algorithm: (similarity * page_rank^0.5 * (amount of matching windows ^ 0.15))
 -- Higher is better
 COALESCE((1 - dist) ^ %(embedding_weight)s * (COALESCE("Page".page_rank, 1) ^ 1.0) * (domain_counts.num_matching_windows ^ (0.20 * %(embedding_weight)s)), -1) as score
  from "Page" INNER JOIN domain_counts ON domain_counts.url = "Page".url  ORDER BY score DESC LIMIT 20
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
    for i, p in enumerate(pages):
        print(f'{i}: Generating embeddings for {p.title} from ({p.url})',)
        data = model.generate_vecs(p.title, p.content, p.url)
        to_append.extend(data)

    cur = db.cursor()
    cur.executemany("""INSERT INTO Embeddings ("url", "index", "vec") VALUES (%s, %s, %s)""", [
                    (x[0], x[1], x[2]) for x in to_append])
    db.commit()


async def generate_embeddings(db: PostgresClient):
    global model

    while True:
        pages = db.cursor(Page).execute(
            '''SELECT p.* FROM "Page" AS p LEFT JOIN Embeddings AS e ON p.url = e.url WHERE e.url IS NULL ORDER BY p.depth ASC LIMIT 50''').fetchall()

        if len(pages) == 0:
            print("ERR: No pages to process")
            return

        await store_embeddings_for_pages(pages)

model = Embedder()


if __name__ == "__main__":
    freeze_support()
    client = PostgresClient()
    client.connect()
    asyncio.run(generate_embeddings(client))
