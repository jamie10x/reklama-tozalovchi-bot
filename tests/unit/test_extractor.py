from app.detector.extractor import (
    extract_text,
    extract_urls,
    extract_mentions,
    extract_entity_urls,
)


class FakeMessageEntity:
    def __init__(self, type_, offset, length, url=None):
        self.type = type_
        self.offset = offset
        self.length = length
        self.url = url


def test_extract_text_basic():
    assert extract_text("hello") == "hello"


def test_extract_text_with_caption():
    result = extract_text(text="text", caption="caption")
    assert result == "text"


def test_extract_text_no_text():
    result = extract_text(text="", caption="caption")
    assert result == "caption"


def test_extract_urls_standard():
    text = "Visit https://example.com/page and http://test.org"
    urls = extract_urls(text)
    assert "https://example.com/page" in urls
    assert "http://test.org" in urls


def test_extract_urls_none():
    text = "Just some text without URLs"
    urls = extract_urls(text)
    assert urls == []


def test_extract_mentions():
    text = "Contact @user123 and @another_user"
    mentions = extract_mentions(text)
    assert "@user123" in mentions
    assert "@another_user" in mentions


def test_extract_mentions_empty():
    text = "No mentions here"
    mentions = extract_mentions(text)
    assert mentions == []


def test_extract_entity_urls():
    text = "Check this link"
    entities = [
        FakeMessageEntity("url", 15, 20),
    ]
    # With offset/length that doesn't match, URLs list may be empty
    entities[0].offset = 6
    entities[0].length = 4
    urls = extract_entity_urls(text, entities)
    assert len(urls) > 0


def test_extract_entity_urls_empty():
    urls = extract_entity_urls("hello", None)
    assert urls == []


def test_extract_urls_multiple():
    text = "Links: https://one.com, https://two.com, https://three.com"
    urls = extract_urls(text)
    assert len(urls) == 3


def test_extract_urls_with_tracking():
    text = "Visit https://example.com?ref=abc&utm_source=telegram"
    urls = extract_urls(text)
    assert len(urls) >= 1
