from typing import Optional, Self
from urllib.parse import urlparse, urlunparse

import validators
from pydantic import BaseModel, validator

SUPPRESSED_DOMAINS = {"wikipedia.org", "amazon.com", "youtube.com", "twitter.com", "facebook.com", "reddit.com",
                      "instagram.com", 'google.com/patent', 'wikimedia.org', 't.co', 'amzn.to', 'github.com',
                      'codeforces.com', 'tandfonline.com', 'wiley.com', 'oup.com', 'sagepub.com', 'sexbuzz.com',
                      'arxiv.org', 'detnews.com', 'cbsnews.com', 'cnn.com', 'scholar.google.com', 'play.google.com',
                      'goo.gl', 'cnevpost.com', 'electrive.com', 'techcrunch.com', 'ssrn.com', 'sciencedirect.com',
                      'springer.com', 'jstor.org', 'nature.com', 'sciencemag.org', 'sciencenews.org',
                      'sciencemuseum.org.uk', 'elifesciences', 'fool.com', 'slimemoldtimemold', 'exfatloss',
                      'achemicalhunger', '9to5toys', 'bloomberg.com', 'forbes.com', 'bbc.com', 'economist.com',
                      'ft.com', 'vimeo.com', 'youtube.com', 'pittsburghlive.com', 'linkedin.com', 'soundcloud.com',
                      'albawa.com', 'theage.com', 'prnewswire.com', 'archive.org', 'stackexchange.com', 'doi.org',
                      'mail-archive.com', 'ncbi.nlm.nih.gov', 'vice.com', 'biorxiv.org', 'psychologytoday.com',
                      'dailymail', 'unsongbook.comgoodreads.com', '.gov', 'knowyourmeme', 'technologyreview.com',
                      'businessinsider.com', 'investopedia.com', 'qualiacomputing.com', 'smithsonianmag.com',
                      'sciencedaily.com', 'plus.google.com', 'genomebiology.biomedcentral.com', 'openid.net',
                      'developer.apple.com', 'cnbc.com', 'brookings.edu', 'thekrazycouponlady.comprinceton.edu',
                      'tvtropes.org', 'theregister.com', 'theonion.com', 'telegraph.co.uk', 'quoteinvestigator.com',
                      'biomedcentral', 'tumblr.com', '9to5google', 'washingtonmonthly', 'ifstudies', 'awardworld.net',
                      'webpronews.com',
                      'brill.com',
                      'caiso.com',
                      'slideshare.net',
                      'stackoverflow.com',
                      'britannica.com',
                      'popsci.com',
                      'christianitytoday.com',
                      'circlinginstitute.com',
                    'avc.com',
                    'baseball-reference.com',
                    'espn.com',
                    'goodreads.com',
                    'greentechmedia.com',
                    'imagen.research.google',
                    'man7.org',
                      'en.wikiquote.org',
                      'actexpo.com',
                      'bmj.com'}

UNSUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx',
                          '.xls', '.xlsx', '.zip', '.rar', '.7z', '.gz', '.png', '.jpg', '.jpeg', }


def is_valid_url(url: str) -> bool:
    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    res = validators.url(url)

    if type(res) == validators.ValidationError:
        return False

    return True


def test_valid():
    assert is_valid_url(
        'http://worrydream.com/ABriefRantOnThefuture0fInteractionDesign/') == True


def clean_url(url: str):
    """Removes hashtags and query parameters from a URL"""
    parsed_url = urlparse(url)

    # Remove hashtags and query parameters
    cleaned_url_parts = parsed_url._replace(fragment='', query='')

    # Reconstruct the cleaned URL
    cleaned_url = urlunparse(cleaned_url_parts)

    return cleaned_url


def get_domain(url: str):
    parsed_url = urlparse(url)

    # Create a new URL without the path
    new_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    return new_url


class Link(BaseModel):
    text: str
    url: str
    parent_url: str | None
    depth: int = 0

    def __lt__(self, other: Self):
        return self.url.__lt__(other.url)

    @classmethod
    def from_url(cls, url: str):
        url = clean_url(url)
        return Link(text="", url=url, parent_url=None, depth=0)

    @validator('url')
    def validate_url(cls, v: str):
        if not is_valid_url(v):
            raise ValueError("Invalid URL: " + v)

        v = clean_url(v)

        return v

    def domain(self) -> str:
        # Parse the URL
        parsed_url = urlparse(self.url)

        # Create a new URL without the path
        new_url = urlunparse(
            (parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        return new_url

    def raw_domain(self) -> str:
        """Returns the domain without the scheme and www prefix"""
        parsed_url = urlparse(self.url)

        # Remove www from the domain if it exists
        if parsed_url.netloc.startswith("www."):
            return parsed_url.netloc[4:]

        return parsed_url.netloc

    def _create_child_link_inner(self, text: str, url: str):
        # TODO: Add support for .pdf files
        if any(url.endswith(ext) for ext in UNSUPPORTED_EXTENSIONS):
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

    def create_child_link(self, text: Optional[str], url: Optional[str]) -> Optional[Self]:
        if url is None:
            return None
        if text is None:
            text = ""
        # Disallow links that are too long. This breaks the PostgreSQL index on the url column
        if len(url) > 2000:
            print(f"Link too long: {url}")
            return None
        try:
            link = self._create_child_link_inner(text, url)
        except ValueError:
            return None

        if link is None:
            return None

        # Check if the url is one of the suppressed domains
        for suppressed in SUPPRESSED_DOMAINS:
            if suppressed in link.url:
                return None

        return link

    def __hash__(self):
        return (self.text,
                self.url,
                self.parent_url,
                self.depth).__hash__()