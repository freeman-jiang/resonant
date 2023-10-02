import functools
from typing import Any, Optional

from nltk import sent_tokenize
from prisma.models import Page
from pydantic import BaseModel


@functools.lru_cache
def sent_tokenize_excerpt(text: str) -> str:
    return text[:350]


class PageResponse(BaseModel):
    id: int
    url: str
    title: str
    excerpt: str
    date: str = ""
    score: Optional[float] = None
    url_only: bool = False

    @classmethod
    def from_prisma_page(cls, p: Page, score=None) -> 'PageResponse':
        # Get first two sentences from p.content
        excerpt = sent_tokenize_excerpt(p.content)

        return PageResponse(
            id=p.id,
            url=p.url,
            title=p.title,
            date=p.date or "",
            excerpt=excerpt,
            score=score
        )

    @classmethod
    def from_page_dict(cls, d: dict[str, Any]) -> 'PageResponse':
        page = Page(**d)
        score = d['score']
        return PageResponse.from_prisma_page(page, score)


class PageResponseURLOnly(BaseModel):
    """
    When a user sends a URL that is not in our database, we don't know the title, url, text...
    """
    url: str
    url_only: bool = True

    # TODO: crawl the page and get the title
