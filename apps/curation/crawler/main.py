import argparse
import asyncio
import time

from .root_urls import ROOT_URLS
from .worker import Worker
from .link import Link

DEFAULT_MAX_LINKS_TO_CRAWL = 200
NUM_WORKERS = 4


async def initialize_queue(queue: asyncio.Queue):
    for root in ROOT_URLS:
        await queue.put(
            Link(text=root["title"], url=root["url"], parent_url="root"))


async def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(prog="python3 -m crawler.main")
    parser.add_argument("--max_links", type=int,
                        help="The maximum number of links to crawl", default=DEFAULT_MAX_LINKS_TO_CRAWL)
    max_links = parser.parse_args().max_links

    shared_queue = asyncio.Queue()
    await initialize_queue(shared_queue)

    # Create a bunch of workers
    workers = [Worker(queue=shared_queue, max_links=20)
               for _ in range(NUM_WORKERS)]
    results = await asyncio.gather(*[worker.run() for worker in workers])

if __name__ == "__main__":
    asyncio.run(main())
