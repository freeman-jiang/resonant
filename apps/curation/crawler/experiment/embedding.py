import asyncio
from functools import cached_property

from psycopg.rows import class_row
import datetime
import os
from typing import Iterator, Any

import numpy as np
import psycopg
import vecs
from sentence_transformers import SentenceTransformer

from crawler.experiment.lda import cluster_documents_with_lda, cluster_documents_with_bertopic
from crawler.link import Link
from crawler.parse import CrawlResult
from dotenv import load_dotenv
from prisma import Prisma, models
from prisma.models import Page

load_dotenv()

client = Prisma()
db = psycopg.connect(os.environ['DATABASE_URL'])


def overlapping_windows(s: str) -> Iterator[str]:
    arr: list[str] = nltk.word_tokenize(s)
    # Generate overlapping windows of size 512 of arr
    for i in range(0, len(arr), 330):
        yield ' '.join(arr[i:i + 380])


def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    similarity = dot_product / (norm_vector1 * norm_vector2)
    return similarity


def compute_cosine_similarity_matrix(vectors):
    num_vectors = vectors.shape[0]
    similarity_matrix = np.zeros((num_vectors, num_vectors))

    for i in range(num_vectors):
        for j in range(num_vectors):
            similarity_matrix[i, j] = cosine_similarity(vectors[i], vectors[j])

    return similarity_matrix


class Embedder:
    model: SentenceTransformer

    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')

    def embed(self, text: str) -> np.ndarray:
        windows = list(overlapping_windows(text))
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


model = SentenceTransformer('all-mpnet-base-v2')
vx = vecs.create_client(os.environ['DATABASE_URL'])

embeddings = vx.get_or_create_collection(name="Embeddings", dimension=768)


def create_index():
    embeddings.create_index(measure=vecs.IndexMeasure.cosine_distance)


def generate_embedding_for_document(document: Page):
    """
    Get embedding for both the document text + title

    :param document:
    :return:
    """

    sentences = nltk.sent_tokenize(document.content)
    model_input = document.title + " " + document.content
    embedding = model.encode(model_input)
    return embedding


class EmbeddingsWithVec(models.Embeddings):
    vec: str
    distance: float



async def query_similar(doc_url: str):
    cursor = db.cursor(row_factory=class_row(EmbeddingsWithVec))
    similar: list[EmbeddingsWithVec] = cursor.execute("""
 WITH want AS (SELECT avg(vec) as vec, url FROM vecs."Embeddings" WHERE url = %s GROUP BY url)

 SELECT distinct ON (e1.url) e1.url, e1.*, e2.avg_dist as distance FROM vecs."Embeddings" e1 RIGHT JOIN (SELECT AVG(e.vec <=> w.vec) as avg_dist, e.url from vecs."Embeddings" as e, want as w WHERE e.url != w.url GROUP BY e.url ORDER BY  avg_dist LIMIT 10) e2
 ON e1.url = e2.url
    """, (doc_url, )).fetchall()



    for sim in similar:
        print("Most similar to ", doc_url, "is:", sim.url, sim.distance)


async def query_similar_test():
    pages = await client.page.find_many(take=100, where={
        'embeddings': {
            'isNot': None
        }
    })

    for p in pages:
        query_similar(p.url)

    return


class PageWithVec(models.Page):
    vec: str

    # def npvec(self):
    #     Convert vec into

async def lda_test():
    # cursor = db.cursor(row_factory=class_row(PageWithVec))
    # pages = cursor.execute("""SELECT * FROM "Page" INNER JOIN "vecs"."Embeddings" ON "Page".url = "vecs"."Embeddings".url LIMIT 100""").fetchall()

    pages = await client.page.find_many(take=950)

    print(cluster_documents_with_bertopic(pages))

    return
async def main():
    model = Embedder()
    await client.connect()
    await lda_test()
    # await query_similar("https://www.evanmiller.org/dont-kill-math.html")
    # return
    # await query_similar_test()
    # return

    while True:
        pages = await client.page.find_many(take=50, where={
            'embeddings': {
                'none': {}
            }
        })

        if len(pages) == 0:
            print("ERR: No pages to process")
            return
        to_append = []
        for p in pages:
            data = model.generate_vecs(p)
            to_append.extend(data)

        query = """INSERT INTO vecs."Embeddings" ("url", "index", "vec") VALUES {}""".format(",".join(
                ["('{}', '{}', '{}')".format(x[0], x[1], x[2]) for x in to_append]))
        print(query)
        await client.execute_raw(query)


import nltk.tokenize

if __name__ == "__main__":
    text = """
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
        """
    #
    # print(model.encode(['this is a sentence', 'and this is another sentence']))
    asyncio.run(main())
