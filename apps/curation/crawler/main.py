import argparse
import asyncio
import time
from prisma import Prisma
from .prisma import PrismaClient

from .link import Link
from .worker import Worker

DEFAULT_MAX_LINKS_TO_CRAWL = 20000
NUM_WORKERS = 12
NUM_DEBUG_WORKERS = 1


async def initialize_queue(prisma: PrismaClient):
    task = await prisma.db.crawltask.find_first()
    if task:
        # Tasks in queue. Good to go
        return

    # No tasks in queue. Add the root URL
    root = Link.from_url('https://hypertext.joodaloop.com/')
    async with prisma.db.tx() as tx:
        await prisma.add_tasks(tx, [root])


async def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(prog="python3 -m crawler.main")
    parser.add_argument("--max_links", type=int,
                        help="The maximum number of links to crawl", default=DEFAULT_MAX_LINKS_TO_CRAWL)
    parser.add_argument("--debug", action="store_true",
                        help="Runs the crawler with a single worker, slowly", default=False)
    max_links = parser.parse_args().max_links
    should_debug = parser.parse_args().debug

    # Initialize Prisma
    db = Prisma()
    await db.connect()
    prisma_client = PrismaClient(db)

    # Initialize the shared work queue
    await initialize_queue(prisma_client)
    done_queue: asyncio.Queue[Link] = asyncio.Queue()
    sentinel_queue: asyncio.Queue[Link] = asyncio.Queue()

    # Create a bunch of workers
    workers = [Worker(
        max_links=max_links,
        done_queue=done_queue,
        sentinel_queue=sentinel_queue,
        should_debug=should_debug,
        prisma=prisma_client)
        for _ in range(NUM_DEBUG_WORKERS if should_debug else NUM_WORKERS)]

    # Start the workers
    tasks = [asyncio.create_task(worker.run()) for worker in workers]

    # When the shared done_queue size reaches max_links, the first worker to reach it
    # will send a sentinel value to this queue
    queue_done = asyncio.create_task(sentinel_queue.get())

    # allow the first exception to bubble up
    workers_done = asyncio.gather(*tasks)

    # Wait for either the queue to be done or the workers to be done
    await asyncio.wait([queue_done, workers_done], return_when=asyncio.FIRST_COMPLETED)

    # Cancel the other task because we just want to shut down
    for task in tasks:
        task.cancel()
    queue_done.cancel()

    await db.disconnect()

    print(
        f"Finished in {time.time() - start_time} seconds. Processed {done_queue.qsize()} links.")

if __name__ == "__main__":
    asyncio.run(main())
