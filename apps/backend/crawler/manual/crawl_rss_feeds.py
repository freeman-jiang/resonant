import datetime

from psycopg.rows import dict_row

from crawler.dbaccess import db
from crawler.link import Link
from crawler.parse import find_feed_urls_cached
from crawler.prismac import PostgresClient

if __name__ == "__main__":
    cursor = db.cursor(row_factory=dict_row)
    rssfeeds = cursor.execute("""
    SELECT url FROM "Rss" WHERE url NOT LIKE 'no rss found%' AND last_crawled_at < NOW() - INTERVAL '1 week'
    """).fetchall()

    rssfeeds = [x['url'] for x in rssfeeds]

    pc = PostgresClient()

    pc.connect()

    curtime = datetime.datetime.now().isoformat()
    for feed in rssfeeds:
        links = find_feed_urls_cached(Link.from_url_raw(feed))
        num_links = pc.add_tasks(links)
        print("Added", num_links, "links from", feed)

        cursor.execute("""
        UPDATE "Rss" SET last_crawled_at = %s WHERE url = %s
        """, (curtime, feed))

        db.commit()

