import argparse
import asyncio
import time

from .root_urls import ROOT_URLS
from .worker import Worker
from .link import Link

DEFAULT_MAX_LINKS_TO_CRAWL = 200


async def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(prog="python3 -m crawler.main")
    parser.add_argument("--max_links", type=int,
                        help="The maximum number of links to crawl", default=DEFAULT_MAX_LINKS_TO_CRAWL)
    max_links = parser.parse_args().max_links

    shared_queue = asyncio.Queue()

    worker = await Worker.create(
        queue=shared_queue, max_links=max_links, root_urls=ROOT_URLS)

    print(f"Starting crawler with max_links: {max_links}\n")
    await worker.run()
    print(
        f"Finished in {time.time() - start_time} seconds. Processed {worker.links_processed} links.")


if __name__ == "__main__":
    asyncio.run(main())
