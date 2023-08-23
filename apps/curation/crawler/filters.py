import requests
from nltk import sent_tokenize, word_tokenize

from crawler.link import Link
from crawler.parse import CrawlResult, parse_html


def should_keep(crawl: CrawlResult) -> bool:
    sentences = sent_tokenize(crawl.content)
    words = word_tokenize(crawl.content)
    avg_sent_len = len(words) / len(sentences)
    avg_word_len = sum(len(word) for word in words) / len(words)

    # TODO: include the variance of sentence lengths too as bad websites have tons of short / tons of long sentences due
    # to ads, bad formatting.
    # Articles have a meaningful sentence length distribution
    return len(sentences) >= 8 and len(words) >= 150 and avg_word_len > 3 and avg_sent_len >= 8 and avg_sent_len <= 50


def test_1():
    link = Link.from_url("http://www.paulgraham.com/pypar.html")

    response = requests.get(link.url)
    text = parse_html(response.content.decode('utf-8', errors='ignore'), link)
    should_keep(text)
    text = text.content
    print(text)

    sentences = sent_tokenize(text)
    words = word_tokenize(text)

    avg_word_len = sum(len(word) for word in words) / len(words)

    # [print(len(x)) for x in sentences]
