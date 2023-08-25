from prisma import Prisma
from .link import Link
from .parse import CrawlResult


class PrismaClient:
    db: Prisma

    def __init__(self, db: Prisma):
        """Prisma Client assumes you have already awaited db.connect() before passing db in"""
        self.db = db

    async def store_page(self, crawl_result: CrawlResult):
        page = await self.db.page.create(data={
            'url': crawl_result.link.url,
            'parent_url': crawl_result.link.parent_url,
            'title': crawl_result.title,
            'date': crawl_result.date,
            'author': crawl_result.author,
            'content': crawl_result.content,
            'outbound_urls': [link.url for link in crawl_result.outgoing_links]
        })
        print(f"PRISMA: Added page to db: {page.url}")
