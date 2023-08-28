import crawler.link as link


def test_is_valid_url():
    assert (link.is_valid_url("https://www.google.com"))
    assert (link.is_valid_url("https://hypertext.joodaloop.com/"))
    assert (not link.is_valid_url("ws://www.something.com"))
    assert (not link.is_valid_url("www.something.com"))
    assert (not link.is_valid_url('http://example.com/">user@example.com'))
