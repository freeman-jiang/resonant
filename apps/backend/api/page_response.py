from typing import Optional

from nltk import sent_tokenize
from prisma.models import Page
from pydantic import BaseModel


class PageResponse(BaseModel):
    id: int
    url: str
    title: str
    excerpt: str
    date: str = ""
    score: Optional[float] = None

    @classmethod
    def from_prisma_page(cls, p: Page, score = None) -> 'PageResponse':
        # Get first two sentences from p.content
        excerpt = sent_tokenize(p.content)[:2]

        return PageResponse(
            id=p.id,
            url=p.url,
            title=p.title,
            date=p.date or "",
            excerpt='. '.join(excerpt),
            score = score
        )
