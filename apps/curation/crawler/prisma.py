from prisma import Json, Prisma

from crawler.config import Config
from .link import Link
from .parse import CrawlResult
from prisma.enums import TaskStatus
from prisma.models import CrawlTask
from prisma.types import CrawlTaskCreateWithoutRelationsInput
from prisma.errors import UniqueViolationError, TransactionExpiredError


class PrismaClient:
    db: Prisma
    cfg: Config

    def __init__(self, cfg: Config, db: Prisma):
        """Prisma Client assumes you have already awaited db.connect() before passing db in"""
        self.db = db
        self.cfg = cfg

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
        links_to_add = [
            l for l in result.outgoing_links if l.depth <= self.cfg.max_crawl_depth]
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

        await self.db.query_raw("BEGIN;")
        tasks = await self.db.query_raw(
            """
            UPDATE "CrawlTask" 
            SET status = $1::"TaskStatus"
            WHERE id = (
                SELECT id FROM "CrawlTask"
                WHERE status::text = $2
                ORDER BY depth ASC, id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING *;
            """,
            TaskStatus.PROCESSING,
            TaskStatus.PENDING,
            model=CrawlTask
        )
        await self.db.query_raw("COMMIT;")
        if not tasks:
            return None

        return tasks[0]

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
