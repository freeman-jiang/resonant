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

    pc = PostgresClient()
    pc.connect()

    response = requests.get(KAGI_FEED_URLS)
    urls = response.text.split('\n')

    started = False
    for url in urls:
        print("Processing", url)
        if started:
            domain = Link.from_url(url).domain()

            if pc.query(f'''SELECT 1 FROM "CrawlTask" WHERE url LIKE '%{domain}%' LIMIT 1''') is not None:
                print("Skipping", url)
                continue
            links = find_feed_urls_cached(Link.from_url(url))
            print(links)
            pc.add_tasks(links)

        if url == 'https://bombthrower.com/feed/':
            started = True
    return urls

if __name__ == "__main__":
    asyncio.run(add_kagi_urls())
