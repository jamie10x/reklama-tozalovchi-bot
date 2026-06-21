from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AIClassificationResult:
    is_advertisement: bool = False
    confidence: float = 0.0
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    summary: str | None = None
    model: str | None = None
    provider: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "is_advertisement": self.is_advertisement,
            "confidence": self.confidence,
            "score": self.score,
            "reasons": self.reasons,
            "summary": self.summary,
            "model": self.model,
            "provider": self.provider,
        }
