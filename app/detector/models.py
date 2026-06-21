from dataclasses import dataclass, field


@dataclass
class DetectionResult:
    is_advertisement: bool = False
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    detected_domains: list[str] = field(default_factory=list)
    detected_telegram_entities: list[str] = field(default_factory=list)


@dataclass
class SecurityResult:
    is_threat: bool = False
    score: int = 0
    severity: str = "low"
    reasons: list[str] = field(default_factory=list)
    detected_indicators: dict[str, list[str]] = field(default_factory=dict)
