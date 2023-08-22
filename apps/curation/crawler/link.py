from typing import Optional, Self
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, model_validator

SUPPRESSED_DOMAINS = {
    "wikipedia.org", "amazon.com", "youtube.com", "twitter.com", "facebook.com", "reddit.com", "instagram.com", 'google.com/patent', 'wikimedia.org',
    't.co', 'amzn.to', 'github.com', 'codeforces.com', 'tandfonline.com', 'wiley.com', 'oup.com', 'sagepub.com', 'sexbuzz.com', 'arxiv.org',
    'detnews.com', 'cbsnews.com', 'cnn.com', 'scholar.google.com', 'play.google.com', 'goo.gl', 'cnevpost.com', 'electrive.com', 'techcrunch.com',
    'ssrn.com', 'sciencedirect.com', 'springer.com', 'jstor.org', 'nature.com', 'sciencemag.org', 'sciencenews.org', 'sciencemuseum.org.uk',
    'bloomberg.com', 'forbes.com', 'bbc.com', 'economist.com', 'ft.com', 'vimeo.com', 'youtube.com',
    'pittsburghlive.com'
}


def is_valid_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


class Link(BaseModel):
    text: str
    url: str
    parent_url: str

    depth: int = 0

    @model_validator(mode='after')
    def validate_url(self):
        if not is_valid_url(self.url):
            raise ValueError("Invalid URL: " + self.url)
        return self

    def domain(self):
        # Parse the URL
        parsed_url = urlparse(self.url)

        # Create a new URL without the path
        new_url = urlunparse(
            (parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        return new_url

    def _create_child_link_inner(self, text: str, url: str):
        # TODO: Add support for .pdf files
        if ".pdf" in url:
            return None

        if is_valid_url(url):
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
            url = self.url + '/' + url
            return Link(text=text, url=url, parent_url=self.url, depth=self.depth + 1)

    def create_child_link(self, text: str, url: str) -> Optional[Self]:
        if url is None:
            return None
        if text is None:
            text = ""
        link = self._create_child_link_inner(text, url)

        if link is None:
            return None

        # Check if the url is one of the suppressed domains
        for suppressed in SUPPRESSED_DOMAINS:
            if suppressed in link.url:
                return None

        return link
