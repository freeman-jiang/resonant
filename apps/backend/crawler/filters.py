import re
from typing import Tuple, List

import pytest
from nltk import sent_tokenize, word_tokenize, LineTokenizer
from prisma import Prisma
from crawler.constants.whitelist import WHITELIST_DOMAINS

from crawler.link import Link
from crawler.parse import CrawlResult


def is_comment_page(crawl: CrawlResult) -> bool:
    regex = r'.*\/comments?(\/|\Z)'
    return bool(re.match(regex, crawl.link.url))


def tokenize_by_line(text: str) -> Tuple[List[str], List[int]]:
    line_tokenizer = LineTokenizer(blanklines='discard')
    tokenized_lines = line_tokenizer.tokenize(text)
    tokenized_lines = [word_tokenize(line) for line in tokenized_lines]
    line_lengths = [len(line) for line in
                    tokenized_lines]  # Calculate line lengths for calculations *without* filtering out short lines

    tokenized_lines = [line for line in tokenized_lines if len(
        line) >= 8]  # Remove too short lines
    flattened_tokens = [
        token for tokens in tokenized_lines for token in tokens]  # Flatten tokens

    return flattened_tokens, line_lengths


def filter_by_line_length(lengths: List[int]) -> bool:
    # If there are no lines, filter this page out because it has no content
    # This check is also needed for the next check to avoid a division by zero error
    if len(lengths) == 0:
        return True

    # We must have a `PERCENT_GREATER` percent of lines with word count >= `THRESHOLD`
    THRESHOLD = 8
    PERCENT_GREATER = 0.75

    # Or we can have lots of long, high quality lines that contribute to >= 65% of the word count

    # Define a high quality line as one with >= 80 words
    long_lines = sum(length for length in lengths if length >= 80)

    if long_lines / len(lengths) >= 0.65:
        return False

    return not (sum(int(length >= THRESHOLD) for length in lengths) / len(lengths) >= PERCENT_GREATER)


def should_keep(crawl: CrawlResult) -> bool:
    """Decide whether or not to keep a page after crawling it based on its content"""
    if crawl.link.raw_domain() in WHITELIST_DOMAINS:
        return True

    if is_comment_page(crawl):
        return False

    words, line_lengths = tokenize_by_line(crawl.content)

    if filter_by_line_length(line_lengths):
        return False

    sentences = sent_tokenize(crawl.content)
    avg_sent_len = len(words) / len(sentences)
    avg_word_len = sum(len(word) for word in words) / len(words)

    return len(sentences) >= 15 and len(words) >= 300 and avg_word_len > 3 and avg_sent_len >= 8 and avg_sent_len <= 100


@pytest.mark.asyncio
async def test_1():
    client = Prisma()
    await client.connect()
    pages = await client.page.find_many(take=500, where={
        'url': 'https://shkspr.mobi/blog/2014/07/'
    })
    for page in pages:
        crawl = CrawlResult(link=Link.from_url(page.url),
                            content=page.content, outbound_links=[])
        if not should_keep(crawl):
            print("Will filter out", page.url)
            pass

def test_2():
    url = 'https://charlesyang.substack.com/p/notes-on-japanese-political-economy'
    cr = CrawlResult.testing_crawl_link(url)
    print(should_keep(cr))
