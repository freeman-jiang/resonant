import asyncio
from queue import Empty as QueueEmpty
from asyncio import Queue, PriorityQueue
from typing import Optional, TypeAlias, Tuple

from aiohttp import ClientError, ClientSession

from . import filters
from .database import Database
from .link import Link
from .parse import CrawlResult, parse_html

MAX_DEPTH = 8
db = Database(CrawlResult, "my_database")
seen_links = Database(Link, "seen_links")


class LinkQueue:
    # Allows us to crawl by priority in the future based on various metrics
    # Retrieve entries by lowest depth first
    queue: PriorityQueue[Tuple[int, Link]]

    def __init__(self):
        self.queue = PriorityQueue()

    async def put(self, link: Link):
        """Only put in links if they haven't been explored before"""
        if not seen_links.contains(link.url):
            seen_links.store(link.url, link)
            await self.queue.put((link.depth, link))

    # Implement empty, get, put, qsize
    def empty(self):
        return self.queue.empty()

    def qsize(self):
        return self.queue.qsize()

    async def get(self) -> Link:
        return (await self.queue.get())[1]


class Worker:
    work_queue: LinkQueue
    done_queue: Queue
    max_links: int
    done: bool
    links_processed: int
    sentinel_queue: Queue
    should_debug: bool

    def __init__(self, *, max_links: int, work_queue: LinkQueue, done_queue: Queue, sentinel_queue: Queue, should_debug: bool = False):
        self.done_queue = done_queue
        self.work_queue = work_queue
        self.max_links = max_links
        self.done = False
        self.links_processed = 0
        self.sentinel_queue = sentinel_queue
        self.should_debug = should_debug

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
        print(f"Links processed: {self.done_queue.qsize()}")
        print(f"Queue size: {self.work_queue.qsize()}")

    async def run_sequential(self):
        """Get, crawl, and parse links from the queue one at a time"""
        async with ClientSession() as session:
            spoof_chrome_user_agent(session)

            while not self.done:
                self.print_status()
                link = await self.work_queue.get()
                print(
                    f"Working on: {link.url} from parent: {link.parent_url} at depth: {link.depth}")
                await self.process_link(link, session)
                print()
                if self.should_debug:
                    await asyncio.sleep(1.5)

            print("Worker exiting...")
            return

    async def process_link(self, link: Link, session: ClientSession) -> Optional[int]:
        """Given `link`, this function crawls and attempts to parse it, then adds any outgoing links to `queue`. Returns the number of links added to `queue` if successful, or `None` if not."""
        response = db.get(link.url, allow_null=True)
        if not response:
            try:
                response = await self.crawl(link, session)
                if not response:
                    await self.done_queue.put(True)
                    print(f"FAILED: Could not crawl {link.url}")
                    return None

                if filters.should_keep(response):
                    print(f"SUCCESS: {link.url}")
                    db.store(link.url, response)
                else:
                    print(f"WARN: Filtered out link: {link.url}")
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
        for l in links_to_add:
            await self.work_queue.put(l)
        print(
            f"SUCCESS: adding {len(links_to_add)} new links from: {link.url}")
        return len(links_to_add)

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
