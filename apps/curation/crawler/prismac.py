from prisma import Prisma
from typing import Optional


from crawler.config import Config
from .link import Link
from .parse import CrawlResult
from prisma.enums import TaskStatus
from prisma.models import CrawlTask, Page
from prisma.types import CrawlTaskCreateWithoutRelationsInput
from prisma.errors import UniqueViolationError
import mmh3


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

    async def add_outgoing_links(self, links: list[Link]):
        links_to_add = [
            l for l in links if l.depth <= self.cfg.max_crawl_depth]
        count = await self.add_tasks(links_to_add)
        print(f"PRISMA: Added {count} tasks to db")

    async def store_raw_page(self, crawl_result: CrawlResult):
        content_hash = str(mmh3.hash128(
            crawl_result.content, signed=False))

        # Check prisma.errors.UniqueViolationError: Unique constraint failed on the fields: (`content_hash`)
        try:
            page = await self.db.page.upsert(
                data={
                    'create': {
                        'content_hash': content_hash,
                        'url': crawl_result.link.url,
                        'parent_url': crawl_result.link.parent_url,
                        'title': crawl_result.title,
                        'date': crawl_result.date,
                        'author': crawl_result.author,
                        'content': crawl_result.content,
                        'outbound_urls': [link.url for link in crawl_result.outbound_links]
                    },
                    'update': {}
                },
                where={
                    'content_hash': content_hash
                }
            )
            return page

        except UniqueViolationError as e:
            if "content_hash" not in str(e):
                raise  # only re-raise if it's not a content_hash error
            return None

    async def store_page(self, task: CrawlTask, crawl_result: CrawlResult) -> Optional[Page]:
        try:
            # TODO: Currently these actions are not done in a transaction. Ideally they are
            # But prisma is very buggy with transactions right now, returning 422 errors
            # They also don't support transactions in raw queries

            page = await self.store_raw_page(crawl_result)
            await self.finish_task(task)
            await self.add_outgoing_links(crawl_result.outbound_links)
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

    async def is_already_explored(self, url: str) -> bool:
        v = await self.db.crawltask.find_first(
            where={
                'parent_url': url,
            }
        )

        return v is not None
