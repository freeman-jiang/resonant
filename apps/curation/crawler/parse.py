import json

import re
from typing import Optional

import newspaper
import trafilatura
from pydantic import BaseModel, validator

from crawler.link import Link
from bs4 import BeautifulSoup


class CrawlResult(BaseModel):
    link: Link
    title: Optional[str]
    date: Optional[str]
    author: Optional[str]
    content: str  # Markdown
    outgoing_links: list[Link]

    @validator('content')
    def validate(cls, v):
        assert len(v) < 2 ** 25, "Content too large to store in database"
        return v


def parse_html_newspaper(html: str, link: Link) -> Optional[CrawlResult]:
    article = newspaper.Article(link.url, keep_article_html=True)
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
    links = [link.create_child_link(element.text, element.get('href'))
             for element in link_elements]
    links = filter(lambda k: k is not None, links)

    publish_date = article.publish_date.isoformat(
    ) if article.publish_date is not None else None

    return CrawlResult(
        link=link,
        title=article.title,
        date=publish_date,
        author=str(article.authors),
        content=article.text,
        outgoing_links=list(links)
    )


def parse_html_trafilatura(html: str, link: Link) -> Optional[CrawlResult]:
    # html = sanitize(html)
    content = trafilatura.extract(html, url=link.url, include_links=True, include_tables=True, output_format='json',
                                  with_metadata=True)

    if content is None:
        return None
    content = json.loads(content)

    # links = extract_links_from_markdown(content['text'], link)
    links = extract_links_from_html(html, link)

    return CrawlResult(
        link=link,
        title=content['title'],
        date=content['date'],
        author=content['author'],
        content=content['text'],
        outgoing_links=links
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
    links = filter(lambda k: k is not None, links)
    return list(links)


def parse_html(html: str, link: Link) -> Optional[CrawlResult]:

    a = parse_html_trafilatura(html, link)
    if a is None:
        a = parse_html_newspaper(html, link)
    return a


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
