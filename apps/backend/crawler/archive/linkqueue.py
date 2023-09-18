from asyncio import PriorityQueue
from typing import Tuple
from crawler.database import Database
from crawler.link import Link
from crawler.parse import CrawlResult

db = Database(CrawlResult, "my_database")
seen_links = Database(Link, "seen_links")


class LinkQueue:
    # Allows us to crawl by priority in the future based on various metrics
    # Retrieve entries by lowest depth first
    queue: PriorityQueue[Tuple[int, Link]]

    def __init__(self):
        self.queue = PriorityQueue()

    async def put(self, link: Link):
        """Only put in links if they haven't been explored before"""
        if not seen_links.contains(link.url):
            seen_links.store(link.url, link)
            await self.queue.put((link.depth, link))

    # Implement empty, get, put, qsize
    def empty(self):
        return self.queue.empty()

    def qsize(self):
        return self.queue.qsize()

    async def get(self) -> Link:
        return (await self.queue.get())[1]
