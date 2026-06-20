import pytest

from app.detector.service import DetectionService


class FakeAllowlistRepo:
    def __init__(self):
        self._data = {"domain": [], "telegram_chat": []}

    async def get_by_type(self, chat_uuid, entity_type):
        return self._data.get(entity_type, [])


class TestDetectionService:
    def setup_method(self):
        self.service = DetectionService()
        self.allowlist = FakeAllowlistRepo()

    @pytest.mark.asyncio
    async def test_ad_telegram_invite(self):
        result = await self.service.analyze(
            text="Join our channel: https://t.me/random_channel",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert result.is_advertisement
        assert result.score >= 6

    @pytest.mark.asyncio
    async def test_ad_earn_money(self):
        result = await self.service.analyze(
            text="Earn money every day. DM me for details.",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert result.is_advertisement

    @pytest.mark.asyncio
    async def test_legit_docs(self):
        result = await self.service.analyze(
            text="Python docs: https://docs.python.org",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert not result.is_advertisement

    @pytest.mark.asyncio
    async def test_normal_conversation(self):
        result = await self.service.analyze(
            text="Hello everyone, how are you?",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert not result.is_advertisement

    @pytest.mark.asyncio
    async def test_empty_text(self):
        result = await self.service.analyze(
            text="",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
        )
        assert not result.is_advertisement

    @pytest.mark.asyncio
    async def test_ad_with_caption(self):
        result = await self.service.analyze(
            text="Check out this offer: https://example.com/buy",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert result.is_advertisement

    @pytest.mark.asyncio
    async def test_allows_domain_whitelist(self):
        class AllowlistWithDomain:
            async def get_by_type(self, chat_uuid, entity_type):
                if entity_type == "domain":
                    return [type("obj", (), {"entity_value": "example.com"})()]
                elif entity_type == "telegram_chat":
                    return []
                return []

        result = await self.service.analyze(
            text="Check this: https://example.com/page",
            mode="normal",
            allowlist_repo=AllowlistWithDomain(),
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert not result.is_advertisement

    @pytest.mark.asyncio
    async def test_ad_spaced_telegram_link(self):
        result = await self.service.analyze(
            text="Join t . me / random_channel",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert result.is_advertisement

    @pytest.mark.asyncio
    async def test_referral_detection(self):
        result = await self.service.analyze(
            text="Sign up here: https://example.com?ref=spam123",
            mode="normal",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert result.is_advertisement
        assert "referral_parameter" in (result.reasons or [])

    @pytest.mark.asyncio
    async def test_strict_mode_catches_more(self):
        result = await self.service.analyze(
            text="Check out this offer: https://example.com/buy",
            mode="strict",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert result.is_advertisement

    @pytest.mark.asyncio
    async def test_relaxed_mode_allows_borderline(self):
        result = await self.service.analyze(
            text="Here is a URL: https://example.com",
            mode="relaxed",
            allowlist_repo=self.allowlist,
            chat_uuid="test-uuid",
            sender_id=123,
        )
        assert not result.is_advertisement
