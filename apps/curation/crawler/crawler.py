import asyncio
import json
import re
from queue import Empty
import time
from asyncio.tasks import as_completed
from typing import Optional
from urllib.parse import urlparse, urlunparse

from .root_urls import ROOT_URLS
import trafilatura
from pydantic import BaseModel, model_validator
from multiprocessing import Pool, Queue
from aiohttp import ClientSession, ClientConnectorError, ClientError

from asyncio import get_event_loop
from asyncio import ensure_future, gather

work_queue = Queue()


class Link(BaseModel):
    text: str
    url: str
    parent_url: str

    depth: int = 0

    @model_validator(mode='after')
    def validate_url(self):
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            raise ValueError("Invalid URL: " + self.url)
        return self
    def domain(self):
        # Parse the URL
        parsed_url = urlparse(self.url)

        # Create a new URL without the path
        new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        return new_url

    def child_link(self, text: str, url: str):
        if url.startswith("http://") or url.startswith("https://"):
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)
        elif url.startswith("/"):
            url = self.domain() + url
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)
        elif url.startswith("#"):
            # Ignore anchor links
            return None
        else:
            print("Invalid URL: " + url + " from parent: " + self.url)
            return None


class CrawlResult(BaseModel):
    url: Link
    title: Optional[str]
    date: Optional[str]
    author: Optional[str]
    content: str # Markdown
    outgoing_links: list[Link]

class ToCrawl(BaseModel):
    url: str
    parent_url: str

def parse_html(html: str, url: Link) -> CrawlResult:
    content = trafilatura.extract(html, url=url.url, include_links=True, include_tables=True, output_format='json',
                                  with_metadata=True)

    if content is None:
        print("Failed to parse: " + url.url)
        return None
    content = json.loads(content)

    links = extract_links_from_markdown(content['text'], url)

    return CrawlResult(
        url=url,
        title=content['title'],
        date=content['date'],
        author=content['author'],
        content=content['text'],
        outgoing_links=links
    )


def extract_links_from_markdown(markdown_text: str, parent: Link) -> list[Link]:
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'  # Regular expression pattern for links

    links = []

    # Find all link matches using the pattern
    for match in re.findall(link_pattern, markdown_text):
        link_text, link_url = match
        link = parent.child_link(link_text, link_url)
        if link:
            links.append(link)

    return links

async def query_internal(url: Link, session, queue: Queue):
    print("Working on URL: ", url.model_dump())
    async with session.get(url.url) as response:
        response = await response.read()

        result = parse_html(response, url)

        if result is None:
            return

        for links in result.outgoing_links:
            if links.depth < 4:
                queue.put(links)
        return result

async def query(url: Link, session, queue: Queue):
    try:
        return await query_internal(url, session, queue)
    except ClientError as e:
        print("Failed to connect to: " + url.url + " with error: " + str(e))
        return None





async def run(url_queue: Queue):
    tasks = []

    def check_tasks():
        for f in tasks:
            if f.done():
                tasks.remove(f)
                if f.exception():
                    f.print_stack()
                    f.result()

    async with ClientSession() as session:
        while True:
            try:
                url = url_queue.get(block = False)
            except Empty:
                check_tasks()
                await asyncio.sleep(1.5)
                continue
            check_tasks()
            task = ensure_future(query(url, session, url_queue))
            tasks.append(task)



def aioloop(url_queue: Queue):
    loop = get_event_loop()

    future = ensure_future(run(url_queue))
    return loop.run_until_complete(future)



def next_batch(queue: Queue) -> list[str]:
    batch = []

    while True and len(batch) < 10:
        batch.append(queue.get())

    return batch

def worker_main(queue: Queue = work_queue):
    try:
        print("Worker started")
        queue = work_queue

        # if not queue.empty():
        #     raise RuntimeError("afds")
        aioloop(queue)
    except Exception as e:
        print("Exception!", e)
        raise e

def set_work_queue(queue: Queue):
    global work_queue
    work_queue = queue

def main():
    work_queue.put(Link(text = "Polymath Playbook", url = "https://salman.io/blog/polymath-playbook/", parent_url = "root"))

    WORKERS = 1
    with Pool(WORKERS, set_work_queue, (work_queue,)) as pool:
        workers = [pool.apply_async(worker_main) for _ in range(WORKERS)]

        # for w in workers:
        #     print("Waiting...")
        #     w.wait()
        #     print(w.get())
        pool.close()
        pool.join()

    pool.join()
if __name__ == "__main__":
    main()

# async def crawl(url: str) -> CrawlResult:
#     data = req
#
# def start_crawl(root_urls = None):
#     if root_urls is None:
#         root_urls = ROOT_URLS
#
#     for root_url in root_urls:
#         crawl(root_url)