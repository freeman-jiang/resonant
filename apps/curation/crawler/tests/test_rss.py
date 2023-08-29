import pytest
from crawler.link import Link
from crawler.parse import parse_html
from aiohttp import ClientSession


@pytest.mark.asyncio
async def test_crawl_rss_links():
    async with ClientSession() as session:
        link = Link.from_url(
            "https://www.henrikkarlsson.xyz/p/good-ideas?utm_source=profile&utm_medium=reader2")
        async with session.get(link.url) as response:
            response = await response.read()
            html = response.decode('utf-8', errors='ignore')

            crawl_result, rss_links = parse_html(html, link, True)
            assert (crawl_result is not None)
            assert (len(rss_links) > 0)

            crawl_result, rss_links = parse_html(html, link, False)
            assert (crawl_result is not None)
            assert (len(rss_links) == 0)
