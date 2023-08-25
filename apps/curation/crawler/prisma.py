import random

from prisma import Json, Prisma
from .link import Link
from .parse import CrawlResult
from prisma.enums import TaskStatus
from prisma.models import CrawlTask
from prisma.types import CrawlTaskCreateWithoutRelationsInput
from prisma.errors import UniqueViolationError


class PrismaClient:
    db: Prisma

    def __init__(self, db: Prisma):
        """Prisma Client assumes you have already awaited db.connect() before passing db in"""
        self.db = db

    async def filter_page(self, tx: Prisma, task: CrawlTask):
        await tx.crawltask.update(
            where={
                'id': task.id
            },
            data={
                'status': TaskStatus.FILTERED
            }
        )

    async def fail_page(self, tx: Prisma, task: CrawlTask):
        await tx.crawltask.update(
            where={
                'id': task.id
            },
            data={
                'status': TaskStatus.FAILED
            })

    async def store_page(self, tx: Prisma, task: CrawlTask, crawl_result: CrawlResult):
        try:
            page = await tx.page.create(data={
                'url': crawl_result.link.url,
                'parent_url': crawl_result.link.parent_url,
                'title': crawl_result.title,
                'date': crawl_result.date,
                'author': crawl_result.author,
                'content': crawl_result.content,
                'outbound_urls': [link.url for link in crawl_result.outgoing_links]
            })
            await self.finish_task(tx, task)
            return page
        except UniqueViolationError:
            print(f"EXCEPTION! Page already exists: {crawl_result.link.url}")
            raise

    async def get_task(self, tx: Prisma) -> CrawlTask | None:
        """Get the next link to crawl from the queue in the database"""
        # Order by lowest priority first
        # task = await tx.query_raw(
        #     """
        #     SELECT * FROM "Task"
        #     WHERE status = 'PENDING'
        #     ORDER BY id ASC
        #     FOR UPDATE SKIP LOCKED
        #     LIMIT 1;"""
        # )
        # See: https://github.com/prisma/prisma/issues/16361
        return await tx.crawltask.query_first(
            """
            SELECT * FROM "CrawlTask"
            WHERE status::text = $1
            ORDER BY depth ASC, id ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1;
            """,
            TaskStatus.PENDING
        )

    async def add_tasks(self, tx: Prisma, links: list[Link]):
        await tx.execute_raw("LOCK TABLE \"CrawlTask\";")
        def create_task(link: Link) -> CrawlTaskCreateWithoutRelationsInput:
            return {
                'status': TaskStatus.PENDING,
                'url': link.url,
                'depth': link.depth,
                'parent_url': link.parent_url,
                'text': link.text,
            }

        count = await tx.crawltask.create_many(
            data=[create_task(link) for link in links],
            skip_duplicates=True)
        return count

    async def finish_task(self, tx: Prisma, task: CrawlTask):
        await tx.crawltask.update(
            data={
                'status': TaskStatus.COMPLETED,
            },
            where={
                'id': task.id
            }
        )
