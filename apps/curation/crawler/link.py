from typing import Optional, Self
from urllib.parse import urlparse, urlunparse

import validators
from pydantic import BaseModel, model_validator

from crawler.root_urls import ROOT_URLS

SUPPRESSED_DOMAINS = {
    "wikipedia.org", "amazon.com", "youtube.com", "twitter.com", "facebook.com", "reddit.com", "instagram.com",
    'google.com/patent', 'wikimedia.org',
    't.co', 'amzn.to', 'github.com', 'codeforces.com', 'tandfonline.com', 'wiley.com', 'oup.com', 'sagepub.com',
    'sexbuzz.com', 'arxiv.org',
    'detnews.com', 'cbsnews.com', 'cnn.com', 'scholar.google.com', 'play.google.com', 'goo.gl', 'cnevpost.com',
    'electrive.com', 'techcrunch.com',
    'ssrn.com', 'sciencedirect.com', 'springer.com', 'jstor.org', 'nature.com', 'sciencemag.org', 'sciencenews.org',
    'sciencemuseum.org.uk',
    'bloomberg.com', 'forbes.com', 'bbc.com', 'economist.com', 'ft.com', 'vimeo.com', 'youtube.com',
    'pittsburghlive.com', 'linkedin.com', 'soundcloud.com', 'albawa.com',
    'prnewswire.com'
}


def is_valid_url(url: str) -> bool:
    try:
        return url.startswith("http://") or url.startswith("https://") and validators.url(url)
    except ValueError:
        return False


def clean_url(url):
    """Removes hashtags and query parameters from a URL"""
    parsed_url = urlparse(url)

    # Remove hashtags and query parameters
    cleaned_url_parts = parsed_url._replace(fragment='', query='')

    # Reconstruct the cleaned URL
    cleaned_url = urlunparse(cleaned_url_parts)

    return cleaned_url


def get_domain(url):
    parsed_url = urlparse(url)

    # Create a new URL without the path
    new_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    return new_url


root_url_domains = {get_domain(x["url"]) for x in ROOT_URLS}


class Link(BaseModel):
    text: str
    url: str
    parent_url: str

    depth: float = 0

    def __lt__(self, other):
        return self.url.__lt__(other.url)

    @classmethod
    def from_url(cls, url: str):
        return Link(text="", url=url, parent_url="", depth=0)

    @model_validator(mode='after')
    def validate_url(self):
        global root_url_domains
        if not is_valid_url(self.url):
            raise ValueError("Invalid URL: " + self.url)

        self.url = clean_url(self.url)

        return self

    def domain(self) -> str:
        # Parse the URL
        parsed_url = urlparse(self.url)

        # Create a new URL without the path
        new_url = urlunparse(
            (parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        return new_url

    def _create_child_link_inner(self, text: str, url: str):
        # TODO: Add support for .pdf files
        if url.endswith(".pdf"):
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
        try:
            link = self._create_child_link_inner(text, url)
        except ValueError:
            return None

        if link is None:
            return None

        # if link.domain() in root_url_domains:
        #     # Deduplicate URL
        #     # Reset depth back to 0, because we encountered root domain again
        #     print("Boosting depth--arrived at root domain")
        #     self.depth -= 0.5

        # Check if the url is one of the suppressed domains
        for suppressed in SUPPRESSED_DOMAINS:
            if suppressed in link.url:
                return None

        return link
