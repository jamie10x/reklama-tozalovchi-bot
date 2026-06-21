import pytest

from app.detector.scoring import THRESHOLDS, scoring_pipeline


class FakeAllowlistRepo:
    def __init__(self):
        self.allowlists = {"user": [], "bot": [], "telegram_chat": [], "domain": []}

    def get_by_type(self, chat_uuid, entity_type):
        return self.allowlists.get(entity_type, [])


@pytest.fixture
def allowlist():
    return FakeAllowlistRepo()


def test_ad_telegram_invite_detected(allowlist):
    result = scoring_pipeline(
        text="Join our channel now: https://t.me/random_channel",
        urls=["https://t.me/random_channel"],
        mentions=[],
        telegram_usernames=["random_channel"],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.is_advertisement
    assert result.score >= THRESHOLDS["normal"]


def test_ad_earn_money_detected(allowlist):
    result = scoring_pipeline(
        text="Earn money every day. DM me for details.",
        urls=[],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.is_advertisement
    assert result.score >= THRESHOLDS["normal"]


def test_ad_limited_offer_detected(allowlist):
    result = scoring_pipeline(
        text="Limited offer! Buy cheap Telegram accounts: example.com",
        urls=["example.com"],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.is_advertisement
    assert result.score >= THRESHOLDS["normal"]


def test_ad_subscribe_detected(allowlist):
    result = scoring_pipeline(
        text="Subscribe to @randomchannel for free signals.",
        urls=[],
        mentions=["@randomchannel"],
        telegram_usernames=["randomchannel"],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.is_advertisement
    assert result.score >= THRESHOLDS["normal"]


def test_ad_referral_detected(allowlist):
    result = scoring_pipeline(
        text="Use my referral link: https://example.com/register?ref=12345",
        urls=["https://example.com/register?ref=12345"],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.is_advertisement
    assert "referral_parameter" in (result.reasons or [])


def test_legit_docs_not_detected(allowlist):
    result = scoring_pipeline(
        text="The Python documentation is available at https://docs.python.org",
        urls=["https://docs.python.org"],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert not result.is_advertisement


def test_legit_question_not_detected(allowlist):
    result = scoring_pipeline(
        text="Can someone explain how Telegram invite links work?",
        urls=[],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert not result.is_advertisement


def test_empty_message_not_detected(allowlist):
    result = scoring_pipeline(
        text="",
        urls=[],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert not result.is_advertisement


def test_normal_conversation_not_detected(allowlist):
    result = scoring_pipeline(
        text="Hello everyone, how are you doing today?",
        urls=[],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert not result.is_advertisement


def test_domain_allowlist_reduces_score():
    class AllowlistWithDomain:
        def get_by_type(self, chat_uuid, entity_type):
            if entity_type == "domain":
                return [type("obj", (), {"entity_value": "docs.python.org"})()]
            return []

    result = scoring_pipeline(
        text="Check docs at https://docs.python.org",
        urls=["https://docs.python.org"],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=AllowlistWithDomain(),
        chat_uuid="test-uuid",
    )
    assert not result.is_advertisement


def test_strict_mode_catches_more(allowlist):
    result = scoring_pipeline(
        text="Limited offer at https://example.com/offer",
        urls=["https://example.com/offer"],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="strict",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.score >= THRESHOLDS["strict"]


def test_relaxed_mode_allows_borderline(allowlist):
    result = scoring_pipeline(
        text="Here is a link: https://example.com/article",
        urls=["https://example.com/article"],
        mentions=[],
        telegram_usernames=[],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="relaxed",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.score < THRESHOLDS["relaxed"]


def test_forward_from_linked_chat_not_detected(allowlist):
    result = scoring_pipeline(
        text="Important announcement",
        urls=[],
        mentions=[],
        telegram_usernames=[],
        has_forward=True,
        forward_from_chat_id=100,
        linked_chat_id=100,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.score == 0
    assert not result.is_advertisement


def test_forward_from_unrelated_channel_detected(allowlist):
    result = scoring_pipeline(
        text="Check this out",
        urls=[],
        mentions=[],
        telegram_usernames=[],
        has_forward=True,
        forward_from_chat_id=999,
        linked_chat_id=100,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.score > 0


def test_ad_spaced_link_detected(allowlist):
    result = scoring_pipeline(
        text="Join t . me / random_channel",
        urls=[],
        mentions=[],
        telegram_usernames=["random_channel"],
        has_forward=False,
        forward_from_chat_id=None,
        linked_chat_id=None,
        mode="normal",
        sender_is_bot=False,
        allowlist_repo=allowlist,
        chat_uuid="test-uuid",
    )
    assert result.is_advertisement
    assert result.score >= THRESHOLDS["normal"]
