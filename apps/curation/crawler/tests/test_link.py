from pydantic import ValidationError
import pytest
from crawler.link import *


def test_pydantic_validators():
    with pytest.raises(ValidationError):
        Link.from_url("www.nohttpprefix.com")


def test_is_valid_url():
    assert (is_valid_url("https://www.google.com"))
    assert (is_valid_url("https://hypertext.joodaloop.com/"))
    assert (not is_valid_url("ws://www.something.com"))
    assert (not is_valid_url("www.something.com"))
    assert (not is_valid_url('http://example.com/">user@example.com'))


def test_url_is_cleaned():
    full_url = "https://www.somesite.com/search?q=python#somehash"
    link = Link.from_url(full_url)
    assert (link.url == "https://www.somesite.com/search")


def test_raw_domain():
    l1 = Link.from_url(
        "https://www.henrikkarlsson.xyz/p/effort-pieces?utm_source=profile&utm_medium=reader2")
    assert (l1.raw_domain() == "henrikkarlsson.xyz")

    l2 = Link.from_url("https://hypertext.joodaloop.com/")
    assert (l2.raw_domain() == "hypertext.joodaloop.com")
