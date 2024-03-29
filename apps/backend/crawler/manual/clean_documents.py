from types import SimpleNamespace

from prisma import Prisma
from prisma.models import Page

from crawler.link import SUPPRESSED_DOMAINS

from crawler.prismac import PostgresClient


def is_english(s: str):
    return True


async def clean_crawltask(db: PostgresClient):
    processed = 0

    to_delete = []

    while True:
        pages = db.cursor().execute(
            "SELECT id, parent_url, url FROM \"CrawlTask\" WHERE status='PENDING' and depth=2 ORDER BY \"CrawlTask\".created_at DESC LIMIT 10000 OFFSET %s", (processed,)).fetchall()

        if len(pages) == 0:
            break
        print(f"Processing {len(pages)} pages")
        processed += len(pages)

        for p in pages:
            p = SimpleNamespace(**p)
            for suppressed in SUPPRESSED_DOMAINS:
                if suppressed in p.url or (p.parent_url and suppressed in p.parent_url):
                    to_delete.append(p.id)
            # if not is_english(p.title + " " + p.content):
            #     print("NOT ENGLISH", p.url)
            #     to_delete.append(p.id)

    if len(to_delete) > 0:
        print("Deleting {} pages".format(len(to_delete)))
        print(to_delete)
        db.query(
            "DELETE FROM \"CrawlTask\" WHERE \"CrawlTask\".id = ANY(%s) RETURNING 1", (to_delete,))

        db.conn.commit()

async def main(db: PostgresClient):
    processed = 0

    to_delete = []

    while True:
        pages = db.cursor().execute(
            "SELECT id, parent_url, url FROM \"Page\" ORDER BY \"Page\".created_at WHERE parent_url NOT ILIKE 'user: %' DESC LIMIT 5000 OFFSET %s", (processed,)).fetchall()

        if len(pages) == 0:
            break
        print(f"Processing {len(pages)} pages")
        processed += len(pages)

        for p in pages:
            p = SimpleNamespace(**p)
            for suppressed in SUPPRESSED_DOMAINS:
                if suppressed in p.url or (p.parent_url and suppressed in p.parent_url):
                    to_delete.append(p.id)
            # if not is_english(p.title + " " + p.content):
            #     print("NOT ENGLISH", p.url)
            #     to_delete.append(p.id)

    if len(to_delete) > 0:
        print("Deleting {} pages".format(len(to_delete)))
        print(to_delete)
        db.query(
            "DELETE FROM \"Page\" WHERE \"Page\".id = ANY(%s) RETURNING 1", (to_delete,))

        db.conn.commit()




if __name__ == '__main__':
    import asyncio
    db = PostgresClient()
    db.connect()
    asyncio.run(clean_crawltask(db))
