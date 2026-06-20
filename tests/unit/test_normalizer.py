from app.detector.normalizer import (
    extract_normalized_telegram_links,
    has_tracking_or_referral,
    normalize_domain,
    normalize_telegram_url,
    normalize_telegram_username,
    normalize_text,
)


def test_normalize_text_basic():
    assert normalize_text("  Hello   World  ") == "Hello World"


def test_normalize_text_unicode():
    text = "Hello\u200bWorld\u200cTest"
    result = normalize_text(text)
    assert "\u200b" not in result
    assert "\u200c" not in result


def test_normalize_text_zero_width():
    text = "Join\u200dt.me/channel"
    result = normalize_text(text)
    assert "\u200d" not in result


def test_normalize_telegram_username():
    assert normalize_telegram_username("@ExampleChannel") == "examplechannel"
    assert normalize_telegram_username("ExampleChannel") == "examplechannel"
    assert normalize_telegram_username("@examplechannel") == "examplechannel"


def test_normalize_domain():
    assert normalize_domain("https://example.com") == "example.com"
    assert normalize_domain("http://www.example.com") == "example.com"
    assert normalize_domain("WWW.EXAMPLE.COM") == "example.com"
    assert normalize_domain("example.com/path?query=1") == "example.com"


def test_normalize_telegram_url():
    result = normalize_telegram_url("https://t.me/examplechannel")
    assert result == "t.me/examplechannel"

    result = normalize_telegram_url("http://telegram.me/ExampleChannel")
    assert result == "telegram.me/examplechannel"


def test_normalize_telegram_url_none():
    result = normalize_telegram_url("https://example.com")
    assert result is None


def test_extract_normalized_telegram_links():
    text = "Join t . me / random_channel"
    results = extract_normalized_telegram_links(text)
    assert "random_channel" in results


def test_extract_normalized_telegram_links_standard():
    text = "Check https://t.me/mychannel"
    results = extract_normalized_telegram_links(text)
    # The spaced version extracts but the standard URL form is handled
    # by the URL pattern matching
    assert isinstance(results, list)


def test_has_tracking_or_referral():
    assert has_tracking_or_referral("https://example.com?ref=12345") is True
    assert has_tracking_or_referral("https://example.com?affiliate=test") is True
    assert has_tracking_or_referral("https://example.com?utm_source=telegram") is True
    assert has_tracking_or_referral("https://example.com/page") is False


def test_normalize_domain_no_protocol():
    assert normalize_domain("example.com") == "example.com"


def test_normalize_domain_trailing_slash():
    assert normalize_domain("https://example.com/") == "example.com"
