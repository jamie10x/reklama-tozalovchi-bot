from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.providers import (
    OllamaProvider,
    OpenAIProvider,
    _parse_ollama_response,
    _parse_openai_response,
)


class TestParseOpenAIResponse:
    def test_valid_json_ad(self):
        raw = (
            '{"is_ad": true, "confidence": 0.95, '
            '"reasons": ["link to unknown site"], "summary": "Ad detected"}'
        )
        r = _parse_openai_response(raw, "gpt-4o-mini")
        assert r.is_advertisement is True
        assert r.confidence == 0.95
        assert r.score == 95
        assert r.reasons == ["link to unknown site"]
        assert r.summary == "Ad detected"
        assert r.model == "gpt-4o-mini"
        assert r.provider == "openai"

    def test_valid_json_safe(self):
        raw = '{"is_ad": false, "confidence": 0.02, "reasons": [], "summary": ""}'
        r = _parse_openai_response(raw, "gpt-4o-mini")
        assert r.is_advertisement is False
        assert r.confidence == 0.02
        assert r.score == 2
        assert r.summary is None

    def test_invalid_json(self):
        r = _parse_openai_response("not json", "gpt-4o-mini")
        assert r.error is not None
        assert "invalid JSON" in r.error

    def test_missing_fields(self):
        raw = '{"foo": "bar"}'
        r = _parse_openai_response(raw, "gpt-4o-mini")
        assert r.is_advertisement is False
        assert r.confidence == 0.0
        assert r.score == 0
        assert r.reasons == []


class TestParseOllamaResponse:
    def test_valid_json_ad(self):
        raw = (
            '{"is_ad": true, "confidence": 0.88, '
            '"reasons": ["phishing link"], "summary": "Phishing attempt"}'
        )
        r = _parse_ollama_response(raw, "llama3.2")
        assert r.is_advertisement is True
        assert r.confidence == 0.88
        assert r.score == 88
        assert r.reasons == ["phishing link"]
        assert r.summary == "Phishing attempt"
        assert r.model == "llama3.2"
        assert r.provider == "ollama"

    def test_invalid_json(self):
        r = _parse_ollama_response("{bad json", "llama3.2")
        assert r.error is not None
        assert "invalid JSON" in r.error

    def test_empty_response(self):
        raw = "{}"
        r = _parse_ollama_response(raw, "llama3.2")
        assert r.is_advertisement is False
        assert r.confidence == 0.0
        assert r.reasons == []


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_no_api_key(self):
        p = OpenAIProvider(api_key="")
        r = await p.classify("test message")
        assert r.error is not None
        assert "API key not configured" in r.error

    @pytest.mark.asyncio
    async def test_timeout(self):
        p = OpenAIProvider(api_key="sk-test", timeout=0.01)

        with patch("httpx.AsyncClient.post", side_effect=TimeoutError("timed out")):
            r = await p.classify("test")
            assert r.error is not None

    @pytest.mark.asyncio
    async def test_http_error(self):
        p = OpenAIProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            r = await p.classify("test")
            assert r.error is not None

    def test_name(self):
        p = OpenAIProvider(api_key="sk-test", model="gpt-4")
        assert p.name() == "openai/gpt-4"


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_timeout(self):
        p = OllamaProvider(timeout=0.01)

        with patch("httpx.AsyncClient.post", side_effect=TimeoutError("timed out")):
            r = await p.classify("test")
            assert r.error is not None

    @pytest.mark.asyncio
    async def test_http_error(self):
        p = OllamaProvider()

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Connection refused")
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            r = await p.classify("test")
            assert r.error is not None

    def test_name(self):
        p = OllamaProvider(model="llama3.2")
        assert p.name() == "ollama/llama3.2"

    @pytest.mark.asyncio
    async def test_successful_classification(self):
        p = OllamaProvider(api_url="http://localhost:11434", model="llama3.2", timeout=5.0)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "response": ('{"is_ad": false, "confidence": 0.01, "reasons": [], "summary": ""}')
            }
        )

        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
            r = await p.classify("Hello, how are you?")
            assert r.is_advertisement is False
            assert r.provider == "ollama"
