from ast import mod
import asyncio
from prisma import Json, Prisma
from .link import Link
from .parse import CrawlResult
from prisma.enums import TaskStatus
from prisma.models import Task
from prisma.types import TaskCreateWithoutRelationsInput, LinkCreateWithoutRelationsInput
from prisma.errors import UniqueViolationError
import prisma.models as models


class PrismaClient:
    db: Prisma

    def __init__(self, db: Prisma):
        """Prisma Client assumes you have already awaited db.connect() before passing db in"""
        self.db = db

    async def get_or_store_link(self, tx: Prisma, link: Link) -> models.Link:
        return await tx.link.upsert(
            data={
                'create': {
                    'url': link.url,
                    'text': link.text,
                    'depth': link.depth,
                },
                'update': {}  # do nothing if link already exists
            },
            where={
                'url': link.url
            }
        )

    async def add_outgoing_links(self, tx: Prisma, page: models.Page, outgoing_links: list[Link]):
        tasks = []

        for link in outgoing_links:
            tasks.append(asyncio.create_task(tx.link.upsert(
                data={
                    'create': {
                        'url': link.url,
                        'text': link.text,
                        'depth': link.depth,
                        'outbound_for': {
                            'connect': {
                                'id':  page.id
                            }
                        }
                    },
                    'update': {
                        'outbound_for': {
                            'connect': [{'id': page.id}]
                        }
                    }
                },
                where={
                    'url': link.url
                }
            )))

        await asyncio.gather(*tasks)

    async def store_page(self, tx: Prisma, task: Task, crawl_result: CrawlResult):
        # TODO: It would be really nice to migrate this to connectOrCreate once it's supported
        try:
            # We assume that the page already has a link entry in the database. This should be true
            # for all pages crawled except for the initial ones
            page = await tx.page.create(data={
                'link': {
                    'connect': {
                        'url': crawl_result.link.url
                    }
                },
                'title': crawl_result.title,
                'date': crawl_result.date,
                'author': crawl_result.author,
                'content': crawl_result.content,
            }, include={'link': True})

            await self.add_outgoing_links(tx, page, crawl_result.outgoing_links)
            await self.finish_task(tx, task)
            return page
        except UniqueViolationError:
            print(
                f"EXCEPTION! UniqueViolationError storing page: {crawl_result.link.url}")
            raise

    async def get_task(self, tx: Prisma) -> Task | None:
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
        return await tx.task.query_first(
            """
            SELECT * FROM "Task"
            WHERE status::text = $1
            ORDER BY id ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1;
            """,
            TaskStatus.PENDING
        )

    async def add_tasks(self, tx: Prisma, links: list[Link]):
        def create_task(link: Link) -> TaskCreateWithoutRelationsInput:
            return {
                'status': TaskStatus.PENDING,
                'message': 'crawl',
                'priority': link.depth,
                'payload': Json(link.json()),
            }

        def create_link(link: Link) -> LinkCreateWithoutRelationsInput:
            return {
                'url': link.url,
                'text': link.text,
                'depth': link.depth,
            }

        async with tx.batch_() as batcher:
            batcher.link.create_many(
                data=[create_link(link) for link in links],
                skip_duplicates=True)

            batcher.task.create_many(
                data=[create_task(link) for link in links])

    async def finish_task(self, tx: Prisma, task: Task):
        await tx.task.update(
            data={
                'status': TaskStatus.COMPLETED,
            },
            where={
                'id': task.id
            }
        )
