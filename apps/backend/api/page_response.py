import datetime
import functools
from typing import Any, Optional

from nltk import sent_tokenize
from prisma.models import Message, Page, User
from pydantic import BaseModel


@functools.lru_cache
def sent_tokenize_excerpt(text: str) -> str:
    return text[:650]


class Sender(BaseModel):
    id: str
    first_name: str
    last_name: str
    profile_picture_url: Optional[str]
    sent_on: datetime.datetime

    @classmethod
    def from_message(cls, message: Message):
        sender = message.sender
        assert (sender is not None)
        return Sender(id=sender.id, first_name=sender.first_name, last_name=sender.last_name,
                      profile_picture_url=sender.profile_picture_url, sent_on=message.sent_on)


class PageResponse(BaseModel):
    id: int
    url: str
    title: str
    excerpt: str
    date: str = ""
    senders: list[Sender] = []
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
