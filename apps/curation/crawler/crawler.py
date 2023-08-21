import asyncio
import multiprocessing
import random
import time
from queue import Empty

from multiprocessing import Pool, JoinableQueue as Queue
from aiohttp import ClientSession, ClientError

from asyncio import get_event_loop
from asyncio import ensure_future

from crawler.database import Database
from crawler.link import Link
from crawler.parse import parse_html
from .root_urls import ROOT_URLS

BLOCKED_DOMAINS = ["sexbuzz.com"]

db = Database()
# db.dump()


class GlobalState:
    work_queue: Queue
    done_flag: multiprocessing.Event

    def __init__(self):
        self.work_queue = Queue()
        self.done_flag = multiprocessing.Event()


global_state: GlobalState = GlobalState()

MAX_DEPTH = 8


async def query_internal(url: Link, session, queue: Queue):
    print("Working on URL: ", url.model_dump())
    async with session.get(url.url) as response:
        if not response.ok:
            return None
        response = await response.read()

        result = parse_html(response.decode('utf-8', errors='ignore'), url)

        if result is None:
            return

        return result


async def query(url: Link, session, queue: Queue):
    existing = db.get(url.url, default=True)
    if existing:
        response = existing
    else:
        try:
            response = await query_internal(url, session, queue)
        except ClientError as e:
            print("Failed to connect to: " + url.url + " with error: " + str(e))
            return None

        if response is not None:
            db.store(url.url, response)

    if response is not None:
        for links in response.outgoing_links:
            if links.depth < MAX_DEPTH:
                queue.put(links)


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


async def run(url_queue: Queue):
    tasks = []

    def check_tasks():
        for f in tasks:
            if f.done():
                tasks.remove(f)
                if f.exception():
                    print("EXCEPTION!!")
                    f.print_stack()
                    f.result()
                    global_state.done_flag.set()

                url_queue.task_done()

    backoff = ExponentialBackoff()
    async with ClientSession() as session:
        spoof_chrome_user_agent(session)

        while not global_state.done_flag.is_set():
            try:
                url = url_queue.get(block=False)
            except Empty:
                print("Queue empty...")
                check_tasks()
                await asyncio.sleep(backoff.backoff())
                continue
            backoff.reset()
            check_tasks()
            task = ensure_future(query(url, session, url_queue))
            tasks.append(task)
        print("Exiting...")


def async_loop(url_queue: Queue):
    loop = get_event_loop()

    future = ensure_future(run(url_queue))
    return loop.run_until_complete(future)


def next_batch(queue: Queue) -> list[str]:
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

    num_workers = 3
    with Pool(num_workers, set_work_queue, (global_state,)) as pool:
        workers = [pool.apply_async(worker_main) for _ in range(num_workers)]

        while True:
            for w in workers:
                if w.ready():
                    print("Worker is finished!")
                    print(w.get())
                    workers.remove(w)
            if global_state.done_flag.is_set():
                print("Done flag is set...")
                break
            if global_state.work_queue.empty():
                time.sleep(5)
                if global_state.work_queue.empty():
                    print("Work queue empty, waiting for shutdown")
                    global_state.done_flag.set()
                    break
            else:
                print("Work queue not empty...sleeping")
                time.sleep(5)

        # global_state.work_queue.join()

        print("Work done! waiting for shutdown")
        pool.terminate()
        pool.join()


# logging.basicConfig(level=logging.ERROR)
if __name__ == "__main__":
    main()
