from prisma import Prisma
from .link import Link
from .parse import CrawlResult


class PrismaClient:
    db: Prisma

    def __init__(self, db: Prisma):
        """Prisma Client assumes you have already awaited db.connect() before passing db in"""
        self.db = db

    async def store_link(self, link: Link):
        link_created = await self.db.links.create({
            'url': link.url,
            'depth': link.depth,
            'text': link.text,
            'parent_url': link.parent_url
        })
        print(f"PRISMA: Added link to db: {link_created.url}")

    async def store_article(self, crawl_result: CrawlResult):
        link = crawl_result.link
        article_created = await self.db.articles.create(data={
            'links': {'create': {
                'url': link.url,
                'depth': link.depth,
                'text': link.text,
                'parent_url': link.parent_url
            }},
            'title': crawl_result.title,
            'date': crawl_result.date,
            'author': crawl_result.author,
            'content': crawl_result.content,
        }, include={'links': True})
        print(f"PRISMA: Added article to db: {article_created.links.url}")
