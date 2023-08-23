import argparse
import asyncio
import time

from .root_urls import ROOT_URLS
from .worker import Worker, LinkQueue
from .link import Link

DEFAULT_MAX_LINKS_TO_CRAWL = 20000
NUM_WORKERS = 12


async def initialize_queue(queue: LinkQueue):
    await queue.put(Link.from_url('https://gwern.net/bitcoin-is-worse-is-better'))
    # for root in ROOT_URLS:
    #     await queue.put(
    #         Link(text=root["title"], url=root["url"], parent_url="root"))


async def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(prog="python3 -m crawler.main")
    parser.add_argument("--max_links", type=int,
                        help="The maximum number of links to crawl", default=DEFAULT_MAX_LINKS_TO_CRAWL)
    max_links = parser.parse_args().max_links

    shared_queue = LinkQueue()
    await initialize_queue(shared_queue)
    done_queue = asyncio.Queue()
    sentinel_queue = asyncio.Queue()

    # Create a bunch of workers
    workers = [Worker(work_queue=shared_queue,
                      max_links=max_links,
                      done_queue=done_queue,
                      sentinel_queue=sentinel_queue)
               for _ in range(NUM_WORKERS)]

    # Start the workers
    tasks = [asyncio.create_task(worker.run()) for worker in workers]


    # When the shared done_queue size reaches max_links, the first worker to reach it
    # will send a sentinel value to this queue
    queue_done = sentinel_queue.get()
    workers_done = asyncio.gather(*tasks, return_exceptions=True)

    await asyncio.gather(queue_done, workers_done, return_exceptions=True)

    # # Cancel the workers
    # for task in tasks:
    #     task.cancel()


    print(
        f"Finished in {time.time() - start_time} seconds. Processed {done_queue.qsize()} links.")

if __name__ == "__main__":
    asyncio.run(main())
