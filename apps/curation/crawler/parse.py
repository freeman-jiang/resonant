import functools
import json
from lxml import etree

import trafilatura.feeds

import re
from typing import Optional, cast, Tuple

import newspaper
import trafilatura
from pydantic import BaseModel, validator
from crawler.constants.whitelist import WHITELIST_DOMAINS

from crawler.link import Link
from bs4 import BeautifulSoup


class CrawlResult(BaseModel):
    link: Link
    title: Optional[str]
    date: Optional[str]
    author: Optional[str]
    content: str  # Markdown
    outbound_links: list[Link]

    @validator('content')
    def validate(cls, v):
        assert len(v) < 2 ** 25, "Content too large to store in database"
        return v


def parse_html_newspaper(html: str, link: Link) -> Optional[CrawlResult]:
    article = newspaper.Article(link.url, keep_article_html=True)
    try:
        article.set_html(html)
        article.parse()
    except newspaper.ArticleException:
        return None

    tree = article.clean_top_node

    if tree is None:
        return None
    # Extract all <a> tags that are not sponsored or ugc (user generated content)
    link_elements = tree.xpath(
        "//a[not(@rel = 'ugc' or @rel = 'sponsored' or @rel = 'nofollow')]")

    # Extract href attribute and link text from each <a> tag
    links = [link.create_child_link(element.text, element.get('href'))
             for element in link_elements]
    links = filter(lambda k: k is not None, links)
    links = cast(list[Link], links)

    publish_date = article.publish_date.isoformat(
    ) if article.publish_date is not None else None

    return CrawlResult(
        link=link,
        title=article.title,
        date=publish_date,
        author=str(article.authors),
        content=article.text,
        outbound_links=list(links)
    )


def filter_out_ugc_sponsored(html: bytes) -> str:
    # Parse the HTML content
    tree = etree.HTML(html)

    # Find and remove <a> tags with rel="ugc", "sponsored", or "nofollow"
    links_to_remove = tree.xpath(
        "//a[@rel='ugc' or @rel='sponsored' or @rel='nofollow']")
    for link in links_to_remove:
        # Simply pop the href to prevent crawler from exploring that page
        link.attrib.pop('href')

    # Return the modified HTML content as a string
    return etree.tostring(tree, encoding='unicode')


def parse_html_trafilatura(html: str, link: Link) -> Optional[CrawlResult]:
    content = trafilatura.extract(html, url=link.url, include_links=True, include_tables=False, include_comments=False, include_images=False, output_format='json',
                                  with_metadata=True, favor_precision=True)

    if content is None:
        return None
    content = json.loads(content)

    if link.raw_domain() in WHITELIST_DOMAINS:
        links = extract_links_from_html(html, link)
    else:
        links = extract_links_from_markdown(content["text"], link)

    title = extract_meta_title(html) or content["title"]

    return CrawlResult(
        link=link,
        title=title,
        date=content['date'],
        author=content['author'],
        content=content['raw_text'],
        outbound_links=links
    )


def extract_links_from_html(html: str, link: Link) -> list[Link]:
    links = []
    soup = BeautifulSoup(html, 'lxml')

    # Extract all <a> tags
    link_elements = soup.find_all('a')
    for a in soup.find_all("a"):
        href = a.get("href")
        links.append(href)

    # Extract href attribute and link text from each <a> tag
    links = [link.create_child_link(element.text, element.get('href'))
             for element in link_elements]
    links = list(filter(lambda k: k is not None, links))
    links = cast(list[Link], links)

    # Filter out links that have the same url as the parent
    links = list(filter(lambda k: k.url != link.url, links))

    return links


@functools.lru_cache
def find_feed_urls_cached(base_domain: Link) -> list[str]:
    rss_feed_urls = trafilatura.feeds.find_feed_urls(base_domain.url)

    print(f"Found {len(rss_feed_urls)} RSS links from {base_domain.url}")

    rss_links = [base_domain.create_child_link(
        "Link From RSS", rssurl) for rssurl in rss_feed_urls]
    rss_links = list(filter(lambda k: k is not None, rss_links))
    return rss_links


def parse_html(html: bytes, link: Link, should_rss: bool) -> Tuple[Optional[CrawlResult], list[Link]]:
    html = filter_out_ugc_sponsored(html)
    a = parse_html_trafilatura(html, link)
    if a is None:
        a = parse_html_newspaper(html, link)

    base_domain = Link.from_url(link.domain())

    if should_rss:
        rss_links = find_feed_urls_cached(base_domain)
    else:
        rss_links = []
    return a, rss_links


def extract_links_from_markdown(markdown_text: str, parent: Link) -> list[Link]:
    # Regular expression pattern for links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

    links = []

    # Find all link matches using the pattern
    for match in re.findall(link_pattern, markdown_text):
        link_text, link_url = match
        link = parent.create_child_link(link_text, link_url)
        if link:
            links.append(link)

    return links


def extract_meta_title(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, 'lxml')
    title = soup.find("meta", property="og:title")
    if title:
        return title["content"]  # type: ignore
    title = soup.find('title')
    if title:
        return title.get_text()


def test_1():
    import requests
    content = requests.get("https://www.aldaily.com/essays-and-opinions/?page=3", headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    })
    print(parse_html(content.content, Link.from_url("https://www.aldaily.com/essays-and-opinions/?page=3"), False))
    # print(trafilatura.feeds.find_feed_urls("http://paulgraham.com"))
    # print(trafilatura.sitemaps.sitemap_search("http://paulgraham.com"))
