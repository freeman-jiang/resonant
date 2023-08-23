import asyncio
from queue import Empty as QueueEmpty
from asyncio import Queue
from typing import Optional, TypeAlias

from aiohttp import ClientError, ClientSession

from .database import Database
from .link import Link
from .parse import CrawlResult, parse_html

MAX_DEPTH = 8
db = Database()
LinkQueue: TypeAlias = "Queue[Link]"


class Worker:
    queue: LinkQueue
    max_links: int
    done: bool
    links_processed: int

    def __init__(self, *, max_links: int, queue: LinkQueue):
        self.queue = queue
        self.max_links = max_links
        self.done = False
        self.links_processed = 0

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
            raise e

    def print_status(self):
        print(f"Links processed: {self.links_processed}")
        print(f"Queue size: {self.queue.qsize()}")

    async def run_parallel(self):
        """Send get requests to all links in the queue at the same time"""
        async with ClientSession() as session:
            spoof_chrome_user_agent(session)

            while not self.done:
                self.print_status()
                tasks = []

                # Get all the links that are currently in the queue and crawl them in parallel
                while not self.queue.empty():
                    link = await self.queue.get()
                    tasks.append(asyncio.create_task(
                        self.process_link(link, session)))

                print(f"Working on {len(tasks)} links in parallel...")
                results = await asyncio.gather(*tasks)
                print(
                    f"Finished working on {len(tasks)} links.")
                print(
                    f"Added {sum(filter(None, results))} new links to queue\n")
                await asyncio.sleep(1)

    async def run_sequential(self):
        """Get, crawl, and parse links from the queue one at a time"""
        async with ClientSession() as session:
            spoof_chrome_user_agent(session)

            while not self.done:
                self.print_status()
                link = await self.queue.get()
                print(
                    f"Working on: {link.url} from parent: {link.parent_url}")
                await self.process_link(link, session)
                print()

            print("Worker exiting...")

    async def process_link(self, link: Link, session: ClientSession) -> Optional[int]:
        """Given `link`, this function crawls and attempts to parse it, then adds any outgoing links to `queue`. Returns the number of links added to `queue` if successful, or `None` if not."""
        response = db.get(link.url, allow_null=True)
        if not response:
            try:
                response = await self.crawl(link, session)
                if not response:
                    self.links_processed += 1
                    print(f"FAILED: Could not crawl {link.url}")
                    return None
                db.store(link.url, response)

            except ClientError as e:
                print(
                    f"FAILED: Can't connect to `{link.url}`, error: `{e}`")
                return None

        self.links_processed += 1
        if self.links_processed >= self.max_links:
            print(f"TARGET LINKS REACHED: {self.max_links}")
            self.done = True
            return None

        # Add outgoing links to queue
        links_to_add = [
            l for l in response.outgoing_links if l.depth < MAX_DEPTH
        ]
        for l in links_to_add:
            await self.queue.put(l)
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
