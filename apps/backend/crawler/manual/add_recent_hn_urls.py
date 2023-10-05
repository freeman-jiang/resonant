import asyncio

from prisma import Prisma

from crawler.config import Config
from crawler.link import Link
from crawler.parse import find_feed_urls_cached
from crawler.prismac import PostgresClient

from dotenv import load_dotenv
load_dotenv()


# Get stories >= 80 points and 30 comments
rssfeeds = ['https://hnrss.org/newest?points=80&comments=30&count=100', 'https://lobste.rs/rss']


async def get_rss_feed():
    pc = PostgresClient()
    pc.connect()

    for rssfeed in rssfeeds:
        links = find_feed_urls_cached(Link.from_url_raw(rssfeed))
        pc.add_tasks(links)


if __name__ == "__main__":
    asyncio.run(get_rss_feed())
