import asyncio

from prisma import Prisma

from crawler.config import Config
import os
from datetime import datetime

import psycopg
from crawler.prismac import PostgresClient

from crawler.recommendation.embedding import store_embeddings_for_pages
from crawler.link import Link
from crawler.parse import CrawlResult

TOPICS = [
    "philosophy", "health", "science", "technology", "politics"
]


# async def seed_database_topics(client: PrismaClient):
#     pages = []
#     for t in TOPICS:
#         cr = CrawlResult(
#             # Use our own domain to store topics
#             # When we serve feeds, don't include anything from our domain
#             link=Link.from_url(
#                 f"https://{t}.topics.superstack-web.vercel.app"),
#             author="Topic: " + t,
#             title="",
#             date=datetime.now().isoformat(),
#             content=t,
#             outbound_links=[]
#         )
#
#         pages.append(client.store_raw_page(1, cr))
#
#     print("Stored pages", pages)
#     await store_embeddings_for_pages(pages)


async def main():
    config = Config()
    db = Prisma()
    await db.connect()
    client = PostgresClient(config, db)
    await seed_database_topics(client)

if __name__ == "__main__":
    asyncio.run(main())
