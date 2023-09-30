import asyncio

import requests
from prisma import Prisma

from crawler.config import Config
from crawler.link import Link
from crawler.parse import find_feed_urls_cached
from crawler.prismac import PostgresClient
from dotenv import load_dotenv

load_dotenv()

KAGI_FEED_URLS = 'https://raw.githubusercontent.com/kagisearch/smallweb/main/smallweb.txt'


async def add_kagi_urls():
    config = Config()

    db = Prisma()
    await db.connect()
    pc = PostgresClient(config, db)

    response = requests.get(KAGI_FEED_URLS)
    urls = response.text.split('\n')

    for url in urls:
        if url < 'https://www.boristhebrave.com/feed':
            continue
        links = find_feed_urls_cached(Link.from_url(url))
        print(links)
        await pc.add_tasks(links)
    return urls

if __name__ == "__main__":
    asyncio.run(add_kagi_urls())
