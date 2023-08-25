import asyncio
from queue import Empty as QueueEmpty
from asyncio import Queue, PriorityQueue
from typing import Optional, TypeAlias, Tuple
from prisma import Prisma
from prisma.models import CrawlTask

from aiohttp import ClientError, ClientSession

from . import filters
from .link import Link
from .parse import CrawlResult, parse_html
from .prisma import PrismaClient

MAX_DEPTH = 8


class Worker:
    done_queue: Queue
    max_links: int
    done: bool
    links_processed: int
    sentinel_queue: Queue
    should_debug: bool
    prisma: PrismaClient

    def __init__(self, *, max_links: int, done_queue: Queue, sentinel_queue: Queue, should_debug: bool = False, prisma: PrismaClient):
        self.done_queue = done_queue
        self.max_links = max_links
        self.done = False
        self.links_processed = 0
        self.sentinel_queue = sentinel_queue
        self.should_debug = should_debug
        self.prisma = prisma

    async def run(self):
        """
        This is the entry point for the worker process which will take items from the work queue, crawl and attempt to parse the link, then add any outgoing links to the work queue.

        The worker will stop adding new outgoing links to the work queue once the number of links processed + the number of links in the work queue is >= `max_links`
        """
        try:
            print("Worker started")
            # for debugging
            await self.run_sequential()
            # await self.run_parallel()
        except Exception as e:
            print(f"Worker encountered exception: {e}")
            self.done = True
            raise

    def print_status(self):
        print(f"Pages processed: {self.done_queue.qsize()}")

    async def run_sequential(self):
        """Get, crawl, and parse links from the queue one at a time"""
        async with ClientSession() as session:
            spoof_chrome_user_agent(session)

            while not self.done:
                self.print_status()

                async with self.prisma.db.tx() as tx:
                    task = await self.prisma.get_task(tx)

                    if task is None:
                        print("No more tasks in database")
                        self.done = True
                        break

                    print(f"Working on task: {task.id}")

                    await self.process_task(tx, task, session)
                    print()

                if self.should_debug:
                    await asyncio.sleep(5)

            print("Worker exiting...")
            return

    async def process_task(self, tx: Prisma, task: CrawlTask, session: ClientSession) -> Optional[int]:
        """Given `link`, this function crawls and attempts to parse it, then adds any outgoing links to `queue`. Returns the number of links added to `queue` if successful, or `None` if not."""

        link = Link(url=task.url, parent_url=task.parent_url,
                    depth=task.depth, text=task.text)
        print(
            f"Working on: {link.url} from parent: {link.parent_url} at depth: {link.depth}")
        try:
            response = await self.crawl(link, session)
            if not response:
                await self.done_queue.put(True)
                print(f"FAILED: Could not crawl {link.url}")
                return None

            if filters.should_keep(response):
                page = await self.prisma.store_page(tx, task, response)
                print(f"SUCCESS: Crawled page: {page.url}")
            else:
                print(f"WARN: Filtered out link: {link.url}")
                page = await self.prisma.filter_page(tx, task)
        except ClientError as e:
            print(
                f"FAILED: Can't connect to `{link.url}`, error: `{e}`")
            return None

        await self.done_queue.put(True)
        if self.done_queue.qsize() >= self.max_links:
            print(f"TARGET LINKS REACHED: {self.max_links}")
            self.done = True
            await self.sentinel_queue.put(True)
            return None

        # Add outgoing links to queue
        links_to_add = [
            l for l in response.outgoing_links if l.depth < MAX_DEPTH
        ]
        count = await self.prisma.add_tasks(links_to_add)
        print(f"PRISMA: Added {count} tasks to db")

    async def crawl(self, link: Link, session: ClientSession) -> Optional[CrawlResult]:
        """Crawl and parse the given `link`, returning a `CrawlResult` if successful, or `None` if not"""
        async with session.get(link.url) as response:
            if not response.ok:
                return None
            response = await response.read()
            return parse_html(response.decode('utf-8', errors='ignore'), link)


def spoof_chrome_user_agent(session: ClientSession):
    # or else we get blocked by cloudflare sites
    session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
