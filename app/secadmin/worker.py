from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.activity import ActivityRepository
from app.database.repositories.events import SecurityEventRepository
from app.database.repositories.indicators import IndicatorRepository
from app.database.repositories.outbox import OutboxRepository
from app.database.repositories.users import ObservedUserRepository
from app.database.secadmin_models import SecurityObservationOutbox
from app.database.session import get_secadmin_sessionmaker

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5
CLAIM_BATCH_SIZE = 10
EVENT_RETENTION_DAYS = 90
WORKER_ID_PREFIX = "worker"


def _severity_from_ad_score(score: int) -> str:
    if score >= 10:
        return "high"
    if score >= 6:
        return "medium"
    return "low"


class SecAdminWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None
        self._worker_id = f"{WORKER_ID_PREFIX}-{id(self)}"

    async def _process_batch(self, session: AsyncSession) -> int:
        outbox_repo = OutboxRepository(session)
        event_repo = SecurityEventRepository(session)
        indicator_repo = IndicatorRepository(session)
        user_repo = ObservedUserRepository(session)
        activity_repo = ActivityRepository(session)

        entries = await outbox_repo.claim_next(
            worker_id=self._worker_id,
            batch_size=CLAIM_BATCH_SIZE,
        )

        for entry in entries:
            entry_id = entry.id
            entry_chat_id = entry.chat_id
            entry_message_id = entry.message_id
            try:
                await self._process_entry(
                    entry=entry,
                    event_repo=event_repo,
                    indicator_repo=indicator_repo,
                    user_repo=user_repo,
                    outbox_repo=outbox_repo,
                    activity_repo=activity_repo,
                )
                await session.flush()
            except Exception:
                logger.exception(
                    "Failed to process observation %s (chat=%d msg=%d)",
                    entry_id,
                    entry_chat_id,
                    entry_message_id,
                )
                await session.rollback()
                await outbox_repo.mark_failed(entry_id)
                await session.flush()

        return len(entries)

    async def _process_entry(
        self,
        entry: SecurityObservationOutbox,
        event_repo: SecurityEventRepository,
        indicator_repo: IndicatorRepository,
        user_repo: ObservedUserRepository,
        outbox_repo: OutboxRepository,
        activity_repo: ActivityRepository,
    ) -> None:
        detection_result = entry.detection_result or {}
        ad_result = detection_result.get("ad")
        security_result = detection_result.get("security")

        indicator_ids: list[str] = []

        if ad_result:
            domains = ad_result.get("detected_domains", [])
            for domain in domains:
                indicator = await indicator_repo.upsert(
                    indicator_type="domain",
                    indicator_value=domain.lower(),
                    chat_id=entry.chat_id,
                )
                indicator_ids.append(str(indicator.id))

            tg_entities = ad_result.get("detected_telegram_entities", [])
            for entity in tg_entities:
                etype = "telegram_username"
                val = entity.lower()
                if val.startswith("t.me/") or val.startswith("https://t.me/"):
                    etype = "telegram_chat"
                elif val.startswith("@"):
                    etype = "telegram_username"
                    val = val.lstrip("@")
                indicator = await indicator_repo.upsert(
                    indicator_type=etype,
                    indicator_value=val,
                    chat_id=entry.chat_id,
                )
                indicator_ids.append(str(indicator.id))

        if security_result and security_result.get("is_threat"):
            detected = security_result.get("detected_indicators", {})
            for indicator_type, values in detected.items():
                for value in values:
                    indicator = await indicator_repo.upsert(
                        indicator_type=indicator_type,
                        indicator_value=value.lower(),
                        chat_id=entry.chat_id,
                    )
                    indicator_ids.append(str(indicator.id))

            now = datetime.now(timezone.utc)
            event = await event_repo.create(
                chat_id=entry.chat_id,
                message_id=entry.message_id,
                sender_id=entry.sender_id,
                event_type="security_threat",
                severity=security_result.get("severity", "low"),
                score=security_result.get("score", 0),
                title="Security attention required",
                message_excerpt=entry.text[:500] if entry.text else None,
                detection_reasons={"reasons": security_result.get("reasons", [])},
                detected_indicators={"indicator_ids": indicator_ids},
                ad_score=ad_result.get("score") if ad_result else None,
                security_score=security_result.get("score"),
                expires_at=now + timedelta(days=EVENT_RETENTION_DAYS),
            )

            for indicator_id_str in indicator_ids:
                await self._link_indicator(indicator_repo, event.id, indicator_id_str)

            await activity_repo.link_event(
                entry.chat_id,
                entry.message_id,
                event.id,
                "security_threat",
            )

        elif ad_result and ad_result.get("is_advertisement"):
            now = datetime.now(timezone.utc)
            score = ad_result.get("score", 0)
            event = await event_repo.create(
                chat_id=entry.chat_id,
                message_id=entry.message_id,
                sender_id=entry.sender_id,
                event_type="advertisement",
                severity=_severity_from_ad_score(score),
                score=score,
                title="Advertisement detected",
                message_excerpt=entry.text[:500] if entry.text else None,
                detection_reasons={"reasons": ad_result.get("reasons", [])},
                detected_indicators={"indicator_ids": indicator_ids},
                ad_score=score,
                expires_at=now + timedelta(days=EVENT_RETENTION_DAYS),
            )

            for indicator_id_str in indicator_ids:
                await self._link_indicator(indicator_repo, event.id, indicator_id_str)

            await activity_repo.link_event(
                entry.chat_id,
                entry.message_id,
                event.id,
                "advertisement",
            )

        if entry.sender_id is not None and security_result and security_result.get("is_threat"):
            try:
                extra_score = security_result.get("score", 0)
                current = await user_repo.get_by_telegram_id(entry.sender_id)
                new_risk = (current.risk_score if current else 0) + extra_score
                await user_repo.update_risk_score(entry.sender_id, new_risk)
            except Exception:
                logger.warning("Failed to update risk score for user %d", entry.sender_id)

        await outbox_repo.mark_completed(entry.id)

    async def _link_indicator(
        self,
        indicator_repo: IndicatorRepository,
        event_id: uuid.UUID,
        indicator_id_str: str,
    ) -> None:
        try:
            await indicator_repo.link_to_event(
                event_id=event_id,
                indicator_id=uuid.UUID(indicator_id_str),
            )
        except Exception:
            logger.debug(
                "Failed to link indicator %s to event %s",
                indicator_id_str,
                event_id,
            )

    async def run_once(self) -> int:
        try:
            sm = get_secadmin_sessionmaker()
            async with sm() as session:
                processed = await self._process_batch(session)
                await session.commit()
                return processed
        except RuntimeError:
            return 0
        except Exception:
            logger.exception("Worker run_once failed")
            return 0

    async def _loop(self) -> None:
        logger.info("SecAdmin worker started (worker_id=%s)", self._worker_id)
        while self._running:
            try:
                processed = await self.run_once()
                if processed > 0:
                    logger.debug("Worker processed %d observations", processed)
            except Exception:
                logger.exception("Worker cycle error")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        logger.info("SecAdmin worker stopped")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("SecAdmin worker task created")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("SecAdmin worker stopped")
