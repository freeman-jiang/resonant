from prisma import Prisma
from crawler.parse import find_feed_urls
import requests

from crawler.recommendation.pagerank import url_to_domain
from langdetect import detect

def is_english(s: str):
    return detect(s) == 'en'

async def main():
    client = Prisma()

    await client.connect()

    processed = 0

    to_delete = []

    domains = set()

    while True:
        pages = await client.page.find_many(take=100, skip=processed)
        if len(pages) == 0 or processed >= 600:
            break
        print(f"Processing {len(pages)} pages")
        processed += len(pages)

        for p in pages:
            domains.add(url_to_domain(p.url))
            # for suppressed in SUPPRESSED_DOMAINS:
            #     if suppressed in p.url:
            #         to_delete.append(p.id)
            # if not is_english(p.title + " " + p.content):
            #     print("NOT ENGLISH", p.url)
            #     to_delete.append(p.id)

    for d in domains:
        try:
            # if requests.get("http://" + d + "/rss").status_code != 200:
            #     if requests.get("http://" + d + "/feed").status_code != 200:
            if find_feed_urls("https://" + d) == []:
                print("NO RSS", d)
        except requests.exceptions.ConnectionError:
            print("NO RSS", d)

    if len(to_delete) > 0:
        print("Deleting {} pages".format(len(to_delete)))
        await client.page.delete_many(where={
            'id': {
                'in': to_delete
            }
        })

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
