import json
import re
from typing import Optional

import newspaper
import trafilatura
from pydantic import BaseModel, model_validator

from crawler.link import Link


class CrawlResult(BaseModel):
    url: Link
    title: Optional[str]
    date: Optional[str]
    author: Optional[str]
    content: str  # Markdown
    outgoing_links: list[Link]

    @model_validator(mode='after')
    def validate(self):
        assert len(self.content) < 2 ** 25, "Content too large to store in database"

        return self


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
