import pytest


@pytest.fixture
def sample_texts() -> dict:
    return {
        "ad_telegram_invite": "Join our channel now: https://t.me/random_channel",
        "ad_earn_money": "Earn money every day. DM me for details.",
        "ad_limited_offer": "Limited offer! Buy cheap Telegram accounts: example.com",
        "ad_subscribe": "Subscribe to @randomchannel for free signals.",
        "ad_referral": "Use my referral link and receive a bonus: https://example.com/register?ref=12345",
        "ad_promotion_service": "Advertising services available. Contact @promoter.",
        "ad_investment": "Best investment opportunity. Guaranteed daily profit. Message me now.",
        "ad_spaced_link": "Join t . me / random_channel",
        "legit_docs": "The Python documentation is available at https://docs.python.org",
        "legit_github": "This GitHub repository explains the solution: https://github.com/example/project",
        "legit_question": "Can someone explain how Telegram invite links work?",
        "legit_purchase": "I bought this laptop last year and it works well.",
        "legit_contact_admin": "Please contact our group administrator @official_admin.",
        "legit_news": "Here is the news article we discussed: https://example-news-site.com/article",
        "legit_official_channel": "Our official channel is @approved_channel",
        "empty": "",
        "only_text": "Hello everyone, how are you doing today?",
        "with_price": "This product costs $20. You can buy it from the store.",
    }
