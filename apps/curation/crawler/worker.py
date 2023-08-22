import asyncio
from queue import Empty as QueueEmpty
from queue import Queue
from typing import Optional, TypeAlias

from aiohttp import ClientError, ClientSession

from .database import Database
from .link import Link
from .parse import CrawlResult, parse_html

MAX_DEPTH = 8
db = Database()
LinkQueue: TypeAlias = "Queue[Link]"


class CrawlerState:
    work_queue: LinkQueue
    max_links: int
    done: bool
    no_new_links: bool
    links_processed: int

    def __init__(self, *, max_links: int):
        self.work_queue = Queue()
        self.max_links = max_links
        self.done = False
        self.no_new_links = False
        self.links_processed = 0


async def worker_main(cs: CrawlerState):
    """
    This is the entry point for the worker process which will take items from the work queue, crawl and attempt to parse the link, then add any outgoing links to the work queue.

    The worker will stop adding new outgoing links to the work queue once `max_links` in the crawler state has been reached.
    """
    try:
        print("Worker started")
        await run_worker_sequential(cs)
    except Exception as e:
        print(f"Worker encountered exception: {e}")
        cs.done = True
        raise e


def print_worker_status(cs: CrawlerState):
    print(f"Links processed: {cs.links_processed}")
    print(f"Queue size: {cs.work_queue.qsize()}")


async def run_worker_sequential(cs: CrawlerState):
    queue = cs.work_queue
    async with ClientSession() as session:
        spoof_chrome_user_agent(session)

        while not cs.done:
            print_worker_status(cs)
            try:
                link = queue.get(block=False)
                await process_link(link, session, queue, cs)
            except QueueEmpty:
                cs.done = True

            if not cs.no_new_links:
                if cs.links_processed + cs.work_queue.qsize() >= cs.max_links:
                    print("Reached max links. No longer adding new links to queue.")
                    cs.no_new_links = True
        print("Worker exiting...")


async def process_link(link: Link, session: ClientSession, queue: LinkQueue, cs: CrawlerState):
    """Given `link`, this function crawls and attempts to parse it, then adds any outgoing links to `queue`"""
    print(f"Working on URL: {link.url} from parent: {link.parent_url}")
    response = db.get(link.url, allow_null=True)
    if not response:
        try:
            response = await crawl(link, session)
            if response:
                db.store(link.url, response)
        except ClientError as e:
            print(f"Failed to connect to: `{link.url}` with error: `{e}`")
            return None

    cs.links_processed += 1
    if not response:
        print(f"Failed crawl: {link.url} from {link.parent_url}\n")
        return

    links_to_add = []
    if not cs.no_new_links:
        links_to_add = [
            l for l in response.outgoing_links if l.depth < MAX_DEPTH
        ]

        for l in links_to_add:
            queue.put(l)

        print(
            f"Succeeded crawl: {link.url}. Added {len(links_to_add)} outbound links to queue\n")
    else:
        print(
            f"Succeeded crawl: {link.url}. No longer adding outbound links\n")


async def crawl(link: Link, session: ClientSession) -> Optional[CrawlResult]:
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
