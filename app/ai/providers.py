from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx

from app.ai.models import AIClassificationResult

SYSTEM_PROMPT = (
    "You are a security classifier for Telegram group messages. "
    "Determine if the message contains unauthorized advertising, "
    "spam, scam, or phishing content. "
    'Respond with JSON: {"is_ad": bool, "confidence": 0.0-1.0, '
    '"reasons": [string], "summary": string}. '
    "Be conservative — only flag clear violations."
)


class AIProvider(ABC):
    @abstractmethod
    async def classify(self, text: str) -> AIClassificationResult: ...

    @abstractmethod
    def name(self) -> str: ...


def _parse_openai_response(raw: str, model: str) -> AIClassificationResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return AIClassificationResult(error=f"OpenAI: invalid JSON response: {raw[:200]}")

    is_ad = bool(data.get("is_ad", False))
    confidence = float(data.get("confidence", 0.0))
    reasons = list(data.get("reasons", []))
    summary = str(data.get("summary", "")) if data.get("summary") else None

    return AIClassificationResult(
        is_advertisement=is_ad,
        confidence=confidence,
        score=round(confidence * 100),
        reasons=reasons,
        summary=summary,
        model=model,
        provider="openai",
    )


def _parse_ollama_response(raw: str, model: str) -> AIClassificationResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return AIClassificationResult(error=f"Ollama: invalid JSON response: {raw[:200]}")

    is_ad = bool(data.get("is_ad", False))
    confidence = float(data.get("confidence", 0.0))
    reasons = list(data.get("reasons", []))
    summary = str(data.get("summary", "")) if data.get("summary") else None

    return AIClassificationResult(
        is_advertisement=is_ad,
        confidence=confidence,
        score=round(confidence * 100),
        reasons=reasons,
        summary=summary,
        model=model,
        provider="ollama",
    )


class OpenAIProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        api_url: str = "https://api.openai.com/v1",
        temperature: float = 0.1,
        timeout: float = 15.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._api_url = api_url.rstrip("/")
        self._temperature = temperature
        self._timeout = timeout

    def name(self) -> str:
        return f"openai/{self._model}"

    async def classify(self, text: str) -> AIClassificationResult:
        if not self._api_key:
            return AIClassificationResult(error="OpenAI: API key not configured")

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": self._temperature,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(
                    f"{self._api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                body = resp.json()
                raw = body["choices"][0]["message"]["content"]
                return _parse_openai_response(raw, self._model)
            except httpx.TimeoutException:
                return AIClassificationResult(error="OpenAI: request timed out")
            except httpx.HTTPStatusError as e:
                return AIClassificationResult(error=f"OpenAI: HTTP {e.response.status_code}")
            except Exception as e:
                return AIClassificationResult(error=f"OpenAI: {e}")


class OllamaProvider(AIProvider):
    def __init__(
        self,
        api_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        temperature: float = 0.1,
        timeout: float = 30.0,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._timeout = timeout

    def name(self) -> str:
        return f"ollama/{self._model}"

    async def classify(self, text: str) -> AIClassificationResult:
        payload = {
            "model": self._model,
            "system": SYSTEM_PROMPT,
            "prompt": text,
            "stream": False,
            "options": {"temperature": self._temperature},
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(
                    f"{self._api_url}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                body = resp.json()
                raw = body.get("response", "")
                return _parse_ollama_response(raw, self._model)
            except httpx.TimeoutException:
                return AIClassificationResult(error="Ollama: request timed out")
            except httpx.HTTPStatusError as e:
                return AIClassificationResult(error=f"Ollama: HTTP {e.response.status_code}")
            except Exception as e:
                return AIClassificationResult(error=f"Ollama: {e}")
