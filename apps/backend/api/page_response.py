import functools
from typing import Any, Optional

from nltk import sent_tokenize
from prisma.models import Page, User
from pydantic import BaseModel


@functools.lru_cache
def sent_tokenize_excerpt(text: str) -> str:
    return text[:650]

class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    profile_picture_url: Optional[str]

    @classmethod
    def from_user(cls, user: User):
        return UserResponse(id=user.id, first_name=user.first_name, last_name=user.last_name, profile_picture_url=user.profile_picture_url)


class PageResponse(BaseModel):
    id: int
    url: str
    title: str
    excerpt: str
    date: str = ""
    senders: list[UserResponse] = []
    score: Optional[float] = None
    url_only: bool = False

    @classmethod
    def from_prisma_page(cls, p: Page, score: Optional[int] = None, dont_trim: bool = False) -> 'PageResponse':
        # Get first two sentences from p.content
        excerpt = p.content if dont_trim else sent_tokenize_excerpt(
            p.content)

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
    senders: list[UserResponse] = []

    # TODO: crawl the page and get the title


