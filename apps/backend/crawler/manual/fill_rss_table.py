import feedparser
import requests
from psycopg.rows import dict_row

from crawler.dbaccess import db
from crawler.parse import find_feed_urls_cached


def find_rss_for_domain(domain: str):
    for suffix in ['/rss', '/feed', '/atom.xml']:

        # Parse the RSS feed
        feed_url = "https://" + domain + suffix

        try:
            response = requests.get(feed_url, timeout = 5)
        except requests.exceptions.RequestException:
            continue
        feed = feedparser.parse(response.content)

        urls = []
        for entry in feed.entries:
            if 'link' in entry:
                urls.append(entry.link)

        if len(urls) > 1:
            return feed_url

if __name__ == "__main__":
    cursor = db.cursor(row_factory=dict_row)
    domains = cursor.execute("""
    SELECT
        MIN(p.id) AS ID,
        split_part(split_part(url, '//', 2), '/', 1) AS domain
    FROM
        "Page" p
    GROUP BY
        domain
    ORDER BY id
    """).fetchall()

    domains = [x['domain'] for x in domains]

    rss_links = []
    activated = False
    skip = 0
    for domain in domains:
        if domain == 'www.half-life.com':
            activated = True
        if activated is False:
            continue
        cursor.execute(f"SELECT 1 FROM \"Rss\" WHERE url LIKE '%{domain}%' or url='no rss found-{domain}'")

        if cursor.fetchone():
            print("Already have RSS for", domain)
        else:
            rss = find_rss_for_domain(domain)
            if rss:
                print(domain, rss)
                cursor.execute("""
                        INSERT INTO "Rss" ("url") VALUES (%s)  ON CONFLICT DO NOTHING;
                        """, (rss,))
                db.commit()
            else:
                print("No RSS for", domain)
                cursor.execute("""
                        INSERT INTO "Rss" ("url") VALUES (%s)  ON CONFLICT DO NOTHING;
                        """, (f"no rss found-{domain}",))
                db.commit()

