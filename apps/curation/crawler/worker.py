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


class GlobalState:
    work_queue: LinkQueue
    done: bool

    def __init__(self):
        self.work_queue = Queue()
        self.done = False


# This is the entry point for the worker process which will take items from the global work queue, crawl and attempt to parse the pages and add any outgoing links to the work queue
async def worker_main(global_state: GlobalState):
    try:
        print("Worker started")
        await run_worker_sequential(global_state)
    except Exception as e:
        print(f"Worker encountered exception: {e}")
        global_state.done = True
        raise e


async def run_worker_sequential(global_state: GlobalState):
    queue = global_state.work_queue
    async with ClientSession() as session:
        spoof_chrome_user_agent(session)

        while not global_state.done:
            print(f"Queue size: {queue.qsize()}")

            link = queue.get()
            await process_link(link, session, queue)
        print("Worker exiting...")


async def process_link(link: Link, session: ClientSession, queue: LinkQueue):
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

    if not response:
        print(f"Failed crawl: {link.url} from {link.parent_url}\n")
        return

    links_to_add = [l for l in response.outgoing_links if l.depth < MAX_DEPTH]
    for l in links_to_add:
        queue.put(l)

    print(
        f"Succeeded crawl: For {link.url} found {len(links_to_add)} outbond links to queue\n")


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
