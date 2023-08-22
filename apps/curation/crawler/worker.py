import asyncio
from queue import Empty as QueueEmpty
from queue import Queue
from typing import Optional, TypeAlias

from aiohttp import ClientError, ClientSession

from .database import Database
from .link import Link
from .parse import CrawlResult, parse_html

MAX_DEPTH = 8
SLEEP_TIME = 1
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
        await run_worker(global_state)
    except Exception as e:
        print(f"Worker encountered exception: {e}")
        global_state.done = True
        raise e


async def run_worker(global_state: GlobalState):
    queue = global_state.work_queue
    tasks: list[asyncio.Task[None]] = []

    def check_tasks():
        for t in tasks:
            if t.done():
                tasks.remove(t)
                if t.exception():
                    print("EXCEPTION!!")
                    t.print_stack()
                    t.result()
                    global_state.done = True

                queue.task_done()

    async with ClientSession() as session:
        spoof_chrome_user_agent(session)

        while not global_state.done:
            try:
                link = queue.get(block=False)
            except QueueEmpty:
                print("Queue empty...")
                check_tasks()
                await asyncio.sleep(SLEEP_TIME)
                print("Awake!")
                continue
            check_tasks()
            task = asyncio.create_task(query(link, session, queue))
            tasks.append(task)
        print("Worker exiting...")


async def query(link: Link, session: ClientSession, queue: LinkQueue):
    response = db.get(link.url, allow_null=True)
    if not response:
        try:
            response = await query_internal(link, session)
            if response:
                db.store(link.url, response)
        except ClientError as e:
            print(f"Failed to connect to: `{link.url}` with error: `{e}`")
            return None

    if response:
        for link in response.outgoing_links:
            if link.depth < MAX_DEPTH:
                queue.put(link)


async def query_internal(link: Link, session: ClientSession) -> Optional[CrawlResult]:
    print(f"Working on URL: {link.model_dump()}")
    async with session.get(link.url) as response:
        if not response.ok:
            return None
        response = await response.read()

        result = parse_html(response.decode('utf-8', errors='ignore'), link)

        if result is None:
            return

        return result


def spoof_chrome_user_agent(session: ClientSession):
    # or else we get blocked by cloudflare sites
    session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
