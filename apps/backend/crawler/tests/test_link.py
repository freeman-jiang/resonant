from pydantic import ValidationError
import pytest
from crawler.link import *
from crawler.prismac import PostgresClient
from crawler.worker import fix


def fix_weird_chars():
    db = PostgresClient(None)
    db.connect()

    query = "SELECT id, title FROM \"Page\" ORDER BY id LIMIT %s OFFSET %s"

    update_query = "UPDATE \"Page\" SET title=%s WHERE id=%s"

    processed = 0
    while True:
        results = db.query(query, (500, processed))
        print(processed)
        processed += len(results)

        for p in results:
            p['title'] = fix(p['title'])

        db.cursor().executemany(update_query, [(x['title'], x['id']) for x in results])
        db.conn.commit()

if __name__ == "__main__":
    fix_weird_chars()

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
