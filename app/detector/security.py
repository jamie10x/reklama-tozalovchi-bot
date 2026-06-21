from __future__ import annotations

import logging

from app.detector.extractor import extract_security_indicators
from app.detector.models import SecurityResult

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS: dict[str, int] = {
    "wallet": 8,
    "ip": 4,
    "phone": 5,
    "email": 3,
}

SEVERITY_MAP: dict[str, str] = {
    "wallet": "high",
    "ip": "medium",
    "phone": "high",
    "email": "low",
}

CRITICAL_THRESHOLD = 12
HIGH_THRESHOLD = 8
MEDIUM_THRESHOLD = 4


def _resolve_severity(score: int) -> str:
    if score >= CRITICAL_THRESHOLD:
        return "critical"
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


class SecurityDetector:
    def analyze(self, text: str) -> SecurityResult:
        if not text or not text.strip():
            return SecurityResult()

        indicators = extract_security_indicators(text)
        if not indicators:
            return SecurityResult()

        total_score = 0
        reasons: list[str] = []
        detected: dict[str, list[str]] = {}

        for indicator_type, values in indicators.items():
            weight = SEVERITY_WEIGHTS.get(indicator_type, 1)
            count = len(values)
            indicator_score = weight * count
            total_score += indicator_score
            reasons.append(
                f"{indicator_type}:{','.join(v for v in values[:3])}"
                f"({'x' + str(count) if count > 1 else ''})"
                f"={indicator_score}"
            )
            detected[indicator_type] = values

        severity = _resolve_severity(total_score)
        is_threat = total_score >= MEDIUM_THRESHOLD

        if is_threat:
            logger.info(
                "Security threat detected: score=%d severity=%s indicators=%s",
                total_score,
                severity,
                {k: len(v) for k, v in detected.items()},
            )

        return SecurityResult(
            is_threat=is_threat,
            score=total_score,
            severity=severity,
            reasons=reasons,
            detected_indicators=detected,
        )
