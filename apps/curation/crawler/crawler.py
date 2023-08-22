import asyncio
from multiprocessing import get_context
import multiprocessing
import random
import time
from queue import Empty

from multiprocessing import Pool, JoinableQueue as Queue

from multiprocessing.synchronize import Event
from typing import List, TypeAlias, Optional

import requests
from aiohttp import ClientSession, ClientError

from asyncio import get_event_loop
from asyncio import ensure_future

from .database import Database
from crawler.link import Link
from crawler.parse import parse_html, CrawlResult
from .root_urls import ROOT_URLS


db = Database()

LinkQueue: TypeAlias = "Queue[Link]"


class GlobalState:
    work_queue: LinkQueue
    done_flag: Event

    def __init__(self):
        self.work_queue = Queue()
        self.done_flag = multiprocessing.Event()


global_state: GlobalState = GlobalState()
MAX_DEPTH = 8


async def query_internal(link: Link, session: ClientSession, queue: LinkQueue) -> Optional[CrawlResult]:
    print(f"Working on URL: {link.model_dump()}")
    async with session.get(link.url) as response:
        if not response.ok:
            return None
        response = await response.read()

        result = parse_html(response.decode('utf-8', errors='ignore'), link)

        if result is None:
            return

        return result


async def query(link: Link, session: ClientSession, queue: LinkQueue):
    response = db.get(link.url, allow_null=True)
    if not response:
        try:
            response = await query_internal(link, session, queue)
            if response:
                db.store(link.url, response)
        except ClientError as e:
            print(f"Failed to connect to: `{link.url}` with error: `{e}`")
            return None

    if response:
        for link in response.outgoing_links:
            if link.depth < MAX_DEPTH:
                queue.put(link)


class ExponentialBackoff:
    def __init__(self):
        self.count = 1

    def reset(self):
        self.count = 1

    def backoff(self):
        self.count += 1
        return min(2 ** self.count, 5)


def spoof_chrome_user_agent(session: ClientSession):
    # or else we get blocked by cloudflare sites
    session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'


async def run(queue: LinkQueue):
    tasks: List[asyncio.Task[None]] = []

    def check_tasks():
        for t in tasks:
            if t.done():
                tasks.remove(t)
                if t.exception():
                    print("EXCEPTION!!")
                    t.print_stack()
                    t.result()
                    global_state.done_flag.set()

                queue.task_done()

    backoff = ExponentialBackoff()
    async with ClientSession() as session:
        spoof_chrome_user_agent(session)

        while not global_state.done_flag.is_set():
            try:
                link = queue.get(block=False)
            except Empty:
                print("Queue empty...")
                check_tasks()
                await asyncio.sleep(backoff.backoff())
                continue
            backoff.reset()
            check_tasks()
            task = asyncio.create_task(query(link, session, queue))
            tasks.append(task)
        print("Exiting...")


def async_loop(url_queue: LinkQueue):
    loop = get_event_loop()

    future = ensure_future(run(url_queue))
    return loop.run_until_complete(future)


def next_batch(queue: LinkQueue) -> list[str]:
    batch = []

    while True and len(batch) < 10:
        batch.append(queue.get())

    return batch


def worker_main():
    try:
        print("Worker started")
        async_loop(global_state.work_queue)
    except Exception as e:
        print("Exception!", e)
        global_state.done_flag.set()
        raise e


def set_work_queue(global_state_new: GlobalState):
    global global_state
    global_state = global_state_new


def main():
    global global_state

    for root in ROOT_URLS:
        global_state.work_queue.put(
            Link(text=root["title"], url=root["url"], parent_url="root"))

    set_work_queue(global_state)
    worker_main()
    #
    # while True:
    #     for w in workers:
    #         if w.ready():
    #             print("Worker is finished!")
    #             print(w.get())
    #             workers.remove(w)
    #     if global_state.done_flag.is_set():
    #         print("Done flag is set...")
    #         break
    #     if global_state.work_queue.empty():
    #         time.sleep(5)
    #         if global_state.work_queue.empty():
    #             print("Work queue empty, waiting for shutdown")
    #             global_state.done_flag.set()
    #             break
    #     else:
    #         print("Work queue not empty...sleeping")
    #         time.sleep(5)


if __name__ == "__main__":
    main()


def test_a():
    link = Link(
        text="", url="https://nap.nationalacademies.org/collection/81/diversity-and-inclusion-in-stemm", parent_url="")
    response = requests.get(link.url).content

    result = parse_html(response.decode(
        'utf-8', errors='ignore'), link).content
    print(result)
