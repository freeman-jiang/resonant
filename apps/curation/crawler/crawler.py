import asyncio
import datetime
import json
import multiprocessing
import re
import time
from queue import Empty
from typing import Optional
from urllib.parse import urlparse, urlunparse

import newspaper
import trafilatura
from lxml import etree
from lxml.html import document_fromstring
from lxml.html.clean import Cleaner
from newspaper import Article
from pydantic import BaseModel, model_validator
from multiprocessing import Pool, JoinableQueue as Queue
from aiohttp import ClientSession, ClientError

from asyncio import get_event_loop
from asyncio import ensure_future
import lmdb

from .root_urls import ROOT_URLS

SUPPRESSED_DOMAINS = [
    "wikipedia.org", "amazon.com", "youtube.com", "twitter.com", "facebook.com", "reddit.com", "instagram.com",'google.com/patent'
]


def sanitize(dirty_html):
    cleaner = Cleaner(page_structure=True,
                      meta=True,
                      embedded=True,
                      links=True,
                      style=True,
                      processing_instructions=True,
                      inline_style=True,
                      scripts=True,
                      javascript=True,
                      comments=True,
                      frames=True,
                      forms=True,
                      annoying_tags=True,
                      remove_unknown_tags=True,
                      safe_attrs_only=True,
                      safe_attrs=frozenset(['src', 'color', 'href', 'title', 'class', 'name', 'id']),
                      remove_tags=('span', 'font', 'div')
                      )

    return cleaner.clean_html(dirty_html)


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

    def _child_link_inner(self, text: str, url: str):
        if url.startswith("http://") or url.startswith("https://"):
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)
        elif url.startswith("#"):
            # Ignore anchor links
            return None
        elif url.startswith("mailto:"):
            # Ignore email links
            return None
        elif url.endswith(".onion"):
            return None
        elif url.startswith("//"):
            url = "http:" + url
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)
        elif url.startswith('/'):
            url = self.domain() + url
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)
        else:
            url = self.domain() + '/' + url
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)

    def child_link(self, text: str, url: str):
        if url is None :
            return None
        if text is None:
            text = ""
        link = self._child_link_inner(text, url)

        if link is None:
            return None
        for suppressed in SUPPRESSED_DOMAINS:
            if suppressed in link.domain():
                return None
        return link


class CrawlResult(BaseModel):
    url: Link
    title: Optional[str]
    date: Optional[str]
    author: Optional[str]
    content: str  # Markdown
    outgoing_links: list[Link]


class Database:
    def __init__(self):
        self.db = lmdb.open("my_database", map_size=int(1e9))

    def store(self, key: str, value: CrawlResult):
        with self.db.begin(write=True) as txn:
            value_bytes = value.model_dump_json().encode('utf-8')
            key_bytes = key.encode('utf-8')
            txn.put(key_bytes, value_bytes)

    def get(self, key: str, default=False) -> Optional[CrawlResult]:
        with self.db.begin() as txn:
            key_bytes = key.encode('utf-8')
            value_bytes = txn.get(key_bytes)
            if default and value_bytes is None:
                return None
            if value_bytes is None:
                raise KeyError("Key not found: " + key)
            return CrawlResult.model_validate_json(value_bytes)

    def contains(self, key: str):
        with self.db.begin() as txn:
            key_bytes = key.encode('utf-8')
            value_bytes = txn.get(key_bytes)
            return value_bytes is not None

    def dump(self):
        # Start a read transaction
        with self.db.begin() as txn:
            # Create a cursor to iterate through the keys
            cursor = txn.cursor()

            # Iterate through the keys and print the values
            for key, value in cursor:
                decoded_value = value.decode("utf-8")  # Convert bytes to string
                print(f"Key: {key}, Value: {decoded_value}")


db = Database()


class GlobalState:
    work_queue: Queue
    done_flag: multiprocessing.Event

    def __init__(self):
        self.work_queue = Queue()
        self.done_flag = multiprocessing.Event()


global_state: GlobalState = GlobalState()

MAX_DEPTH = 4


def parse_html_newspaper(html: str, url: Link) -> Optional[CrawlResult]:
    article = newspaper.Article(url.url, keep_article_html=True)
    try:
        article.download()
        article.parse()
    except newspaper.ArticleException:
        return None

    tree = article.clean_top_node

    if tree is None:
        return None
    # Extract all <a> tags
    link_elements = tree.xpath('//a')

    # Extract href attribute and link text from each <a> tag
    links = [url.child_link(element.text, element.get('href')) for element in link_elements]
    links = filter(lambda k: k is not None, links)

    publish_date = article.publish_date.isoformat() if article.publish_date is not None else None


    return CrawlResult(
        url=url,
        title=article.title,
        date=publish_date,
        author=str(article.authors),
        content=article.text,
        outgoing_links=list(links)
    )


def parse_html_trafilatura(html: str, url: Link) -> Optional[CrawlResult]:
    # html = sanitize(html)
    html += "</body></html>"
    content = trafilatura.extract(html, url=url.url, include_links=True, include_tables=True, output_format='json',
                                  with_metadata=True)

    if content is None:
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


def parse_html(html: str, url: Link) -> Optional[CrawlResult]:
    a = parse_html_trafilatura(html, url)
    if a is None:
        a = parse_html_newspaper(html, url)
        if a is None:
            print("Failed to parse: " + url.url + " from" + url.parent_url)
    return a


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
                check_tasks()
                await asyncio.sleep(backoff.backoff())
                continue
            backoff.reset()
            check_tasks()
            task = ensure_future(query(url, session, url_queue))
            tasks.append(task)


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
        _workers = [pool.apply_async(worker_main) for _ in range(num_workers)]

        global_state.work_queue.join()

        global_state.done_flag.set()
        print("Work done! waiting for shutdown")

        # for w in workers:
        #     print("Waiting...")
        #     w.wait()
        #     print(w.get())
        pool.close()
        pool.join()


import trafilatura.external
import logging

# logging.basicConfig(level=logging.ERROR)
if __name__ == "__main__":

    # import cfscrape
    # scraper = cfscraper.create_scraper()  # returns a CloudflareScraper instance
    # # Or: scraper = cfscrape.CloudflareScraper()  # CloudflareScraper inherits from requests.Session
    # print(scraper.get("https://carta.com/blog/carta-101/").content)
    main()
