from dataclasses import dataclass, field


@dataclass
class DetectionResult:
    is_advertisement: bool = False
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    detected_domains: list[str] = field(default_factory=list)
    detected_telegram_entities: list[str] = field(default_factory=list)
