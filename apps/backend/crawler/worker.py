import asyncio
import random
from asyncio import Queue
from typing import Optional, Tuple

import numpy as np
from aiohttp import ClientError, ClientSession, ClientTimeout
from crawler.config import Config
from prisma.models import CrawlTask

from . import filters
from .link import SUPPRESSED_DOMAINS, Link
from .parse import CrawlResult, parse_html
from .prismac import PostgresClient
from .recommendation.embedding import model


class Worker:
    config: Config
    done_queue: Queue[bool]
    done: bool
    sentinel_queue: Queue[bool]
    prisma: PostgresClient
    id: int

    def __init__(self, *, id: int, config: Config, done_queue: Queue[bool], sentinel_queue: Queue[bool], prisma: PostgresClient):
        self.config = config
        self.done_queue = done_queue
        self.done = False
        self.sentinel_queue = sentinel_queue
        self.prisma = prisma
        self.id = id

    async def run(self):
        """
        This is the entry point for the worker process which will take items from the work queue, crawl and attempt to parse the link, then add any outbound links to the work queue.

        The worker will stop adding new outbound links to the work queue once the number of links processed + the number of links in the work queue is >= `max_links`
        """
        try:
            print("Worker started")
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
        # Prevents exhausting the queue and exiting all at once
        await asyncio.sleep(random.uniform(0, 1) * 5)
        async with ClientSession(timeout=ClientTimeout(total=20)) as session:
            spoof_chrome_user_agent(session)

            while not self.done:
                self.print_status()

                task = await self.prisma.get_task()

                if task is None:
                    print("No more tasks in database")
                    self.done = True
                    break

                print(f"Working on task: {task.id}")

                await self.process_task(task, session)

            print("Worker exiting...")
            return

    async def process_task(self, task: CrawlTask, session: ClientSession) -> Optional[CrawlResult]:
        """Given `link`, this function crawls and attempts to parse it, then adds any outbound links to `queue`. Returns the number of links added to `queue` if successful, or `None` if not."""

        link = Link(url=task.url, parent_url=task.parent_url,
                    depth=task.depth, text=task.text)
        print(
            f"Working on: {link.url} from parent: {link.parent_url} at depth: {link.depth}")
        try:
            response, rss_links = await self.crawl(link, session)

            if len(rss_links):
                self.prisma.add_outgoing_links(rss_links)

            if not response:
                await self.done_queue.put(True)
                page = await self.prisma.fail_page(task)
                print(f"FAILED: Could not crawl {link.url}")
                return None

            if link.depth == 0 or filters.should_keep(response):
                page = self.prisma.store_page(task, response)
                if page is not None:
                    print(f"SUCCESS: Crawled page: {page.url}")
            else:
                print(f"WARN: Filtered out link: {link.url}")
                page = await self.prisma.filter_page(task)
        except ClientError as e:
            print(
                f"FAILED: Can't connect to `{link.url}`, error: `{e}`")
            page = await self.prisma.fail_page(task)
            await self.done_queue.put(True)

            return None
        await self.done_queue.put(True)
        if self.done_queue.qsize() >= self.config.max_links:
            print(f"TARGET LINKS REACHED: {self.config.max_links}")
            self.done = True
            await self.sentinel_queue.put(True)
            return None

        return response

    async def crawl(self, link: Link, session: ClientSession) -> Tuple[Optional[CrawlResult], list[Link]]:
        """
        Crawl and parse the given `link`, returning a `CrawlResult` if successful, or `None` if not.
        The second tuple element is a list of RSS links found on that *domain*.
        """
        # should_rss = not await self.prisma.is_already_explored(link.domain())
        # Always false because we manually crawl all RSS links now...
        should_rss = False

        for suppressed in SUPPRESSED_DOMAINS:
            if suppressed in link.url:
                print("Encountered suppressed domain, skipping", link.url)
                return None, []

        try:
            async with session.get(link.url) as response:
                if not response.ok:
                    print("Encountered non-200 response, skipping", response.status)
                    return None, []
                response = await response.read()

                response, rss = parse_html(response, link, should_rss)

                if response is None:
                    print("Encountered parse error, skipping", link.url)
                return response, rss
        except asyncio.TimeoutError:
            print("Encountered timeout, skipping", link.url)
            return None, []


async def crawl_interactive(link: Link) -> Tuple[np.ndarray, CrawlResult] | None:
    """
    Used for realtime search when the user gives us an unknown URL. We need to crawl it right away, calculate the
    embeddings, and return.

    For now, don't add it to our database (as users might submit bad links).
    """

    async with ClientSession(timeout=ClientTimeout(connect=4)) as session:
        spoof_chrome_user_agent(session)

        async with session.get(link.url) as response:
            if not response.ok:
                return None
            response, _rss_links = parse_html(await response.read(), link, False)

        if response is None:
            return None
        return get_window_avg(response.title + " " + response.content), response


# Same as above, but don't calculate embeddings
async def crawl_only(link: Link) -> CrawlResult | None:
    async with ClientSession(timeout=ClientTimeout(connect=4)) as session:
        spoof_chrome_user_agent(session)

        async with session.get(link.url) as response:
            if not response.ok:
                return None
            response, _ = parse_html(await response.read(), link, False)

        if response is None:
            return None

        return response


def get_window_avg(content: str) -> np.ndarray:
    """
    Embed the given content using the sentence-transformers model
    """
    vectors = model.embed(content, for_query=True)

    # Potentially long document, so the first few windows are most representative of what the user wants
    avg_two_windows = np.mean(vectors[:4], axis=0)
    return avg_two_windows


def spoof_chrome_user_agent(session: ClientSession):
    # or else we get blocked by cloudflare sites
    session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'


