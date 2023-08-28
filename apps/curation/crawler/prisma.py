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
            # TODO: Currently these actions are not done in a transaction. Ideally they are
            # But prisma is very buggy with transactions right now, returning 422 errors
            # They also don't support transactions in raw queries
            page = await self.db.page.create(data={
                'url': crawl_result.link.url,
                'parent_url': crawl_result.link.parent_url,
                'title': crawl_result.title,
                'date': crawl_result.date,
                'author': crawl_result.author,
                'content': crawl_result.content,
                'outbound_urls': [link.url for link in crawl_result.outgoing_links]
            })
            await self.finish_task(task)
            await self.add_outgoing_links(crawl_result)
            return page
        except UniqueViolationError:
            print(f"EXCEPTION! Page already exists: {crawl_result.link.url}")
            raise

    async def get_task(self) -> CrawlTask | None:
        """Get the next link to crawl from the queue in the database"""

        # The reason we don't have to wrap this in a transaction is because PostgreSQL
        # actually treats every SQL statement as being executed within a transaction implicitly.
        # That's why we can use `FOR UPDATE SKIP LOCKED`
        # Source: https://www.postgresql.org/docs/current/tutorial-transactions.html#:~:text=PostgreSQL%20actually%20treats,transaction%20block.
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

    async def finish_task(self, task: CrawlTask):
        await self.db.crawltask.update(
            data={
                'status': TaskStatus.COMPLETED,
            },
            where={
                'id': task.id
            }
        )
