import asyncio

import requests
from prisma import Prisma

from crawler.config import Config
from crawler.link import Link
from crawler.parse import find_feed_urls_cached
from crawler.prismac import PrismaClient

from dotenv import load_dotenv
load_dotenv()


# Get stories >= 80 points and 30 comments
rssfeed = 'https://hnrss.org/newest?points=80&comments=30&count=100'


async def get_rss_feed():
    config = Config()

    db = Prisma()
    await db.connect()
    pc = PrismaClient(config, db)

    links = find_feed_urls_cached(Link.from_url(rssfeed))

    await pc.add_tasks(links)


if __name__ == "__main__":
    asyncio.run(get_rss_feed())
