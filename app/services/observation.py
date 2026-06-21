from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.outbox import OutboxRepository
from app.detector.models import DetectionResult, SecurityResult

logger = logging.getLogger(__name__)

OBSERVATION_TEXT_TTL_SECONDS = 86400  # 24 hours


@dataclass
class MessageContext:
    chat_id: int
    message_id: int
    update_id: int
    text: str
    sender_id: int | None = None
    sender_is_bot: bool = False
    sender_chat_id: int | None = None
    is_forwarded: bool = False
    forward_from_chat_id: int | None = None
    ad_result: DetectionResult | None = None
    security_result: SecurityResult | None = None
    ai_result: dict | None = None
    entities: list = field(default_factory=list)
    caption_entities: list = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ObservationProducer:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._outbox_repo = OutboxRepository(session)

    def _should_observe(self, ctx: MessageContext) -> bool:
        if ctx.ad_result is not None and ctx.ad_result.is_advertisement:
            return True
        return ctx.security_result is not None and ctx.security_result.is_threat

    async def produce(self, ctx: MessageContext) -> int | None:
        if not self._should_observe(ctx):
            return None

        if await self._outbox_repo.exists_by_message(ctx.chat_id, ctx.message_id):
            return None

        detection_result: dict | None = None
        if ctx.ad_result is not None:
            detection_result = {
                "is_advertisement": ctx.ad_result.is_advertisement,
                "score": ctx.ad_result.score,
                "reasons": ctx.ad_result.reasons,
                "detected_domains": ctx.ad_result.detected_domains,
                "detected_telegram_entities": ctx.ad_result.detected_telegram_entities,
            }

        security_result: dict | None = None
        if ctx.security_result is not None and ctx.security_result.is_threat:
            security_result = {
                "is_threat": ctx.security_result.is_threat,
                "score": ctx.security_result.score,
                "severity": ctx.security_result.severity,
                "reasons": ctx.security_result.reasons,
                "detected_indicators": ctx.security_result.detected_indicators,
            }

        combined = {}
        if detection_result is not None:
            combined["ad"] = detection_result
        if security_result is not None:
            combined["security"] = security_result
        if ctx.ai_result is not None:
            combined["ai"] = ctx.ai_result

        from datetime import timedelta

        expires_at = ctx.timestamp + timedelta(seconds=OBSERVATION_TEXT_TTL_SECONDS)

        entry = await self._outbox_repo.create(
            update_id=ctx.update_id,
            chat_id=ctx.chat_id,
            message_id=ctx.message_id,
            sender_id=ctx.sender_id,
            text_hash=_compute_text_hash(ctx.text),
            text=ctx.text,
            detection_result=combined if combined else None,
            expires_at=expires_at,
        )

        logger.debug(
            "Observation produced: update_id=%d chat=%d msg=%d sender=%s",
            ctx.update_id,
            ctx.chat_id,
            ctx.message_id,
            ctx.sender_id,
        )

        return entry.id
