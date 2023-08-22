import argparse
import asyncio
import time

from .root_urls import ROOT_URLS
from .worker import CrawlerState, worker_main
from .link import Link

DEFAULT_MAX_LINKS_TO_CRAWL = 200


def add_root_urls(gs: CrawlerState):
    for root in ROOT_URLS:
        gs.work_queue.put(
            Link(text=root["title"], url=root["url"], parent_url="root"))


async def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(prog="python3 -m crawler.main")
    parser.add_argument("--max_links", type=int,
                        help="The maximum number of links to crawl", default=DEFAULT_MAX_LINKS_TO_CRAWL)
    max_links = parser.parse_args().max_links

    cs = CrawlerState(max_links=max_links)
    add_root_urls(cs)
    cs.max_links = max_links

    print(f"Starting crawler with max_links: {max_links}\n")
    await worker_main(cs)
    print(
        f"Finished in {time.time() - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
