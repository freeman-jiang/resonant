import asyncio

from prisma import Prisma

from crawler.config import Config
from crawler.link import Link
from crawler.prisma import PrismaClient

# This script adds additional root URLs to the database work queue. Because they are initialized with
# depth 0 they will be prioritized


async def main():
    config = Config()
    db = Prisma()
    await db.connect()
    pc = PrismaClient(config, db)

    urls = []
    with open("crawler/ROOT_URLS.txt", "r") as f:
        urls = f.readlines()

    links = [Link.from_url(url) for url in urls]
    tasks_created = await pc.add_tasks(links)

    print(
        f"Added {tasks_created} new tasks to the work queue")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
