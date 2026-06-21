from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.ai.models import AIClassificationResult
from app.ai.service import AIService


class TestAIServiceFromConfig:
    def test_disabled(self):
        svc = AIService.from_config(enabled=False)
        assert svc.enabled is False
        assert svc.provider_name is None

    def test_unknown_provider(self):
        svc = AIService.from_config(enabled=True, provider_name="unknown")
        assert svc.enabled is False

    def test_openai_no_key(self):
        svc = AIService.from_config(enabled=True, provider_name="openai", api_key="")
        assert svc.enabled is True
        assert "openai" in (svc.provider_name or "")

    def test_ollama_default(self):
        svc = AIService.from_config(enabled=True, provider_name="ollama")
        assert svc.enabled is True
        assert "ollama" in (svc.provider_name or "")


class TestAIServiceAnalyzeMessage:
    @pytest.mark.asyncio
    async def test_disabled_returns_none(self):
        svc = AIService(enabled=False)
        r = await svc.analyze_message("test", rule_result=None)
        assert r is None

    @pytest.mark.asyncio
    async def test_no_provider_returns_none(self):
        svc = AIService(provider=None, enabled=True)
        r = await svc.analyze_message("test")
        assert r is None

    @pytest.mark.asyncio
    async def test_short_text_returns_none(self):
        provider = AsyncMock()
        provider.classify = AsyncMock(return_value=AIClassificationResult())
        svc = AIService(provider=provider, enabled=True, min_text_length=100)
        r = await svc.analyze_message("short")
        assert r is None
        provider.classify.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_analysis(self):
        provider = AsyncMock()
        expected = AIClassificationResult(
            is_advertisement=True,
            confidence=0.9,
            score=90,
            reasons=["test"],
            model="test-model",
            provider="test",
        )
        provider.classify = AsyncMock(return_value=expected)
        provider.name = lambda: "test/test-model"

        svc = AIService(provider=provider, enabled=True)
        r = await svc.analyze_message("Buy cheap watches now!")

        assert r is expected
        provider.classify.assert_awaited_once_with("Buy cheap watches now!")

    @pytest.mark.asyncio
    async def test_analysis_error(self):
        provider = AsyncMock()
        provider.classify = AsyncMock(return_value=AIClassificationResult(error="API error"))
        provider.name = lambda: "test/model"

        svc = AIService(provider=provider, enabled=True, min_text_length=0)
        r = await svc.analyze_message("test")

        assert r is not None
        assert r.error == "API error"


class TestAddAiResultToDetection:
    def test_no_ai_result(self):
        svc = AIService()
        result = svc.add_ai_result_to_detection({"ad": {"score": 10}}, None)
        assert result == {"ad": {"score": 10}}

    def test_with_ai_result(self):
        svc = AIService()
        ai = AIClassificationResult(is_advertisement=True, confidence=0.9, score=90)
        result = svc.add_ai_result_to_detection({"ad": {"score": 10}}, ai)
        assert result["ad"]["score"] == 10
        assert result["ai"]["is_advertisement"] is True
        assert result["ai"]["confidence"] == 0.9

    def test_no_detection_result(self):
        svc = AIService()
        ai = AIClassificationResult(is_advertisement=True, confidence=0.5, score=50)
        result = svc.add_ai_result_to_detection(None, ai)
        assert result["ai"]["is_advertisement"] is True
