from __future__ import annotations

from typing import Protocol

from app.ai.models import AIClassificationResult
from app.ai.providers import AIProvider, OllamaProvider, OpenAIProvider
from app.core.logging import get_logger
from app.detector.models import DetectionResult

logger = get_logger(__name__)


class AIProviderProto(Protocol):
    async def classify(self, text: str) -> AIClassificationResult: ...

    def name(self) -> str: ...


class AIService:
    def __init__(
        self,
        provider: AIProviderProto | None = None,
        enabled: bool = True,
        min_text_length: int = 10,
    ) -> None:
        self._provider = provider
        self._enabled = enabled
        self._min_text_length = min_text_length

    @classmethod
    def from_config(
        cls,
        enabled: bool = False,
        provider_name: str = "openai",
        api_key: str = "",
        api_url: str = "",
        model: str = "",
    ) -> AIService:
        if not enabled:
            return cls(enabled=False)

        provider: AIProvider | None = None

        if provider_name == "openai":
            provider = OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4o-mini",
                api_url=api_url or "https://api.openai.com/v1",
            )
        elif provider_name == "ollama":
            provider = OllamaProvider(
                api_url=api_url or "http://localhost:11434",
                model=model or "llama3.2",
            )
        else:
            logger.warning("Unknown AI provider: %s, AI disabled", provider_name)
            return cls(enabled=False)

        logger.info(
            "AI service initialized",
            provider=provider.name(),
        )
        return cls(provider=provider, enabled=True)

    async def analyze_message(
        self,
        text: str,
        rule_result: DetectionResult | None = None,
    ) -> AIClassificationResult | None:
        if not self._enabled or self._provider is None:
            return None

        if not text or len(text.strip()) < self._min_text_length:
            return None

        result = await self._provider.classify(text)

        if result.error is not None:
            logger.warning("AI classification error", error=result.error)
            return result

        if result.is_advertisement:
            logger.info(
                "AI flagged ad",
                provider=self._provider.name(),
                confidence=result.confidence,
                reasons=result.reasons,
            )
        else:
            logger.debug(
                "AI: safe",
                provider=self._provider.name(),
                confidence=result.confidence,
            )

        return result

    def add_ai_result_to_detection(
        self,
        detection_result: dict | None,
        ai_result: AIClassificationResult | None,
    ) -> dict | None:
        if ai_result is None:
            return detection_result

        combined = detection_result or {}
        combined["ai"] = ai_result.to_dict()
        return combined

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def provider_name(self) -> str | None:
        if self._provider is not None:
            return self._provider.name()
        return None
