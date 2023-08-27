import random

from prisma import Json, Prisma
from .link import Link
from .parse import CrawlResult
from prisma.enums import TaskStatus
from prisma.models import CrawlTask
from prisma.types import CrawlTaskCreateWithoutRelationsInput
from prisma.errors import UniqueViolationError, TransactionExpiredError


class PrismaClient:
    db: Prisma

    def __init__(self, db: Prisma):
        """Prisma Client assumes you have already awaited db.connect() before passing db in"""
        self.db = db

    async def filter_page(self, task: CrawlTask):
        await self.db.crawltask.update(
            where={
                'id': task.id
            },
            data={
                'status': TaskStatus.FILTERED
            }
        )

    async def fail_page(self, task: CrawlTask):
        await self.db.crawltask.update(
            where={
                'id': task.id
            },
            data={
                'status': TaskStatus.FAILED
            })

    async def add_outgoing_links(self, result: CrawlResult):
        # Add outgoing links to queue
        # TODO: Replace with constant
        links_to_add = [l for l in result.outgoing_links if l.depth < 8]
        count = await self.add_tasks(links_to_add)
        print(f"PRISMA: Added {count} tasks to db")

    async def store_page(self, task: CrawlTask, crawl_result: CrawlResult):
        try:
            async with self.db.tx() as tx:
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

            await self.add_outgoing_links(crawl_result)
            return page
        except UniqueViolationError:
            print(f"EXCEPTION! Page already exists: {crawl_result.link.url}")
            raise

    async def get_task(self) -> CrawlTask | None:
        """Get the next link to crawl from the queue in the database"""

        # Use a transaction to block other workers from getting the same task
        try:
            async with self.db.tx() as tx:
                # See: https://github.com/prisma/prisma/issues/16361
                tasks = await tx.query_raw(
                    """
                        SELECT * FROM "CrawlTask"
                        WHERE status::text = $1
                        ORDER BY depth ASC, id ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                        """,
                    TaskStatus.PENDING,
                    model=CrawlTask
                )

                if tasks is None:
                    return None

                task = tasks[0]
                in_progress_task = await tx.crawltask.update(
                    data={
                        'status': TaskStatus.PROCESSING
                    },
                    where={
                        'id': task.id
                    }
                )

                return in_progress_task
        except TransactionExpiredError as e:
            # We don't re-raise because this exception can be caused by spotty internet
            print(f"EXCEPTION! Transaction expired getting task: {e}")

    async def add_tasks(self, links: list[Link]):
        # await self.db.execute_raw("LOCK TABLE \"CrawlTask\";")

        def create_task(link: Link) -> CrawlTaskCreateWithoutRelationsInput:
            return {
                'status': TaskStatus.PENDING,
                'url': link.url,
                'depth': link.depth,
                'parent_url': link.parent_url,
                'text': link.text,
            }

        count = await self.db.crawltask.create_many(
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
