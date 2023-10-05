import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

import validators
from pydantic import BaseModel, validator

SUPPRESSED_DOMAINS = {"wikipedia.org", "amazon.com", "youtube.com", "twitter.com", "facebook.com", "reddit.com",
                      "instagram.com", 'google.com/patent', 'wikimedia.org', 'https://t.co', 'amzn.to',
                      'codeforces.com', 'tandfonline.com', 'wiley.com', 'oup.com', 'sagepub.com', 'sexbuzz.com',
                      'arxiv.org', 'detnews.com', 'cbsnews.com', 'cnn.com', 'scholar.google.com', 'play.google.com',
                      'goo.gl', 'cnevpost.com', 'electrive.com', 'techcrunch.com', 'ssrn.com', 'sciencedirect.com',
                      'springer.com', 'jstor.org', 'nature.com', 'sciencemag.org', 'sciencenews.org',
                      'sciencemuseum.org.uk', 'elifesciences', 'fool.com', 'slimemoldtimemold', 'exfatloss',
                      'achemicalhunger', '9to5toys', 'bloomberg.com', 'forbes.com', 'bbc.com', 'economist.com',
                      'vimeo.com', 'youtube.com', 'pittsburghlive.com', 'linkedin.com', 'soundcloud.com',
                      'albawa.com', 'theage.com', 'prnewswire.com', 'archive.org', 'stackexchange.com', 'doi.org',
                      'jamanetwork',
                      'versobooks.com',

                      'www.sitepoint.com',

                      'youtu.be',

                      'developer.mozilla.org',
                      'code.jquery.com',
                      'css-tricks.com',
                      'completemusicupdate.com',
                        'feeds.feedblitz.com',
                      'https://stop.zona-m.net',
                      'finance.yahoo.com',
                      'voanews.com',
                      'rust-lang.org',
                      'foxnews.com',
                      'www.codevscolor.com',
                      'https://www.cerealously.net',
                      'tv-vcr.com',
                      'w3.org/',
                      'bbc.co.uk/n',
                      'docs.djangoproject.com',
                      'ghost.org',
                      'codepen.io/',
                      'freecodecamp.org/',
                      'inverse.com',
                      'radiofreemormon.org',
                      'https://www.rapamycin.news',
                      'vg247.com',
                      'podcasts.apple.com',
                      'demonstrations.wolfram.com',
                      'statesummaries.ncics.org',
                      'machinelearning.apple.com',
                      'news.asu.edu',
                      'dl.acm.org',
                      'law.cornell.edu',
                      'grammy.com',
                      'lemonde.fr',
                      'newscience.org',
                      'ew.com',
                      'sqlite.org',
                      'healthline.com',
                      'cs.cmu.edu',
                      'mbl.edu',
                      'euronews.com',
                      'proteinatlas.org',
                      'rockpapershotgun.com',
                      'fandom.com',
                      'mail-archive.com', 'ncbi.nlm.nih.gov', 'vice.com', 'biorxiv.org', 'psychologytoday.com',
                      'dailymail', 'unsongbook.com', 'goodreads.com', '.gov', 'knowyourmeme', 'technologyreview.com',
                      'businessinsider.com', 'investopedia.com', 'qualiacomputing.com', 'smithsonianmag.com',
                      'sciencedaily.com', 'plus.google.com', 'genomebiology.biomedcentral.com', 'openid.net',
                      'developer.apple.com', 'cnbc.com', 'brookings.edu', 'thekrazycouponlady.com', 'princeton.edu',
                      'tvtropes.org', 'theregister.com', 'theonion.com', 'telegraph.co.uk', 'quoteinvestigator.com',
                      'biomedcentral', 'tumblr.com', '9to5google', 'washingtonmonthly', 'ifstudies', 'awardworld.net',
                      'webpronews.com',
                      'webmd.com',

                      'sleeplessbeastie.eu',
                      'thewhitepube.co.uk',
                      'raymii.org',

                      'brill.com',
                      'https://github.com/',
                      'http://github.com/',
                      'ramii.org',
                      'americansongwriter.com',
                        ''
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

emoj = re.compile("["
                  u"\U0001F600-\U0001F64F"  # emoticons
                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                  u"\U00002500-\U00002BEF"  # chinese char
                  u"\U00002702-\U000027B0"
                  u"\U000024C2-\U0001F251"
                  u"\U0001f926-\U0001f937"
                  u"\U00010000-\U0010ffff"
                  u"\u2640-\u2642"
                  u"\u2600-\u2B55"
                  u"\u200d"
                  u"\u23cf"
                  u"\u23e9"
                  u"\u231a"
                  u"\ufe0f"  # dingbats
                  u"\u3030"
                  "]+", re.UNICODE)


def _remove_emojis(data):
    return re.sub(emoj, '', data)


def is_valid_url(url: str) -> bool:
    url = _remove_emojis(url)
    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    res = validators.url(url)

    if type(res) == validators.ValidationError:
        return False

    return True


def test_valid():
    assert is_valid_url(
        'http://worrydream.com/ABriefRantOnThefuture0fInteractionDesign/') == True

    assert is_valid_url('https://nautil.us/your-🧠-on-emoji-365823/') == False


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
    raw: bool = False
    text: str
    url: str
    parent_url: str | None
    depth: int = 0

    def __lt__(self, other: 'Link'):
        return self.url.__lt__(other.url)

    @classmethod
    def from_url(cls, url: str):
        url = clean_url(url)
        return Link(text="", url=url, parent_url=None, depth=0)

    @classmethod
    def from_url_raw(cls, url: str):
        return Link(text="", url=url, parent_url=None, depth=0, raw=True)

    @validator('url')
    def validate_url(cls, v: str, values):
        if not is_valid_url(v):
            raise ValueError("Invalid URL: " + v)
        if values['raw']:
            return v
        else:
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

    def create_child_link(self, text: Optional[str], url: Optional[str]) -> Optional['Link']:
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


def test_suppressed():
    for suppressed in SUPPRESSED_DOMAINS:
        if suppressed in 'https://bayesianbiologist.com/2020/04/20/the-treachery-of-models/':
            print(suppressed)
