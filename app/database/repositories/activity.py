from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.secadmin_models import GroupCaptureSetting, ObservedMessage

CAPTURE_METADATA_ONLY = "metadata_only"
CAPTURE_FLAGGED_ONLY = "flagged_only"
CAPTURE_FULL_TEXT = "full_text"
CAPTURE_MODES = {CAPTURE_METADATA_ONLY, CAPTURE_FLAGGED_ONLY, CAPTURE_FULL_TEXT}


def _hash_text(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_settings(self, chat_id: int) -> GroupCaptureSetting:
        stmt = select(GroupCaptureSetting).where(GroupCaptureSetting.chat_id == chat_id)
        result = await self._session.execute(stmt)
        settings = result.scalar_one_or_none()
        if settings is not None:
            return settings
        settings = GroupCaptureSetting(chat_id=chat_id)
        self._session.add(settings)
        await self._session.flush()
        return settings

    async def update_settings(
        self,
        chat_id: int,
        enabled: bool | None = None,
        capture_mode: str | None = None,
        metadata_retention_days: int | None = None,
        flagged_retention_days: int | None = None,
        updated_by_officer_id: int | None = None,
    ) -> GroupCaptureSetting:
        settings = await self.get_or_create_settings(chat_id)
        if enabled is not None:
            settings.enabled = enabled
        if capture_mode is not None:
            if capture_mode not in CAPTURE_MODES:
                raise ValueError(f"Unsupported capture mode: {capture_mode}")
            settings.capture_mode = capture_mode
        if metadata_retention_days is not None:
            settings.metadata_retention_days = max(1, min(metadata_retention_days, 3650))
        if flagged_retention_days is not None:
            settings.flagged_retention_days = max(1, min(flagged_retention_days, 3650))
        settings.updated_by_officer_id = updated_by_officer_id
        settings.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return settings

    async def record_message(
        self,
        chat_id: int,
        message_id: int,
        text: str | None,
        sender_id: int | None = None,
        sender_username: str | None = None,
        sender_first_name: str | None = None,
        sender_last_name: str | None = None,
        sender_is_bot: bool = False,
        sender_chat_id: int | None = None,
        message_type: str = "text",
        is_edited: bool = False,
        is_forwarded: bool = False,
        forward_from_chat_id: int | None = None,
        reply_to_message_id: int | None = None,
        entities: dict | None = None,
        detection_status: str = "clean",
        risk_score: int = 0,
        ad_score: int | None = None,
        security_score: int | None = None,
        ai_score: int | None = None,
        detection_result: dict | None = None,
        message_date: datetime | None = None,
    ) -> ObservedMessage | None:
        settings = await self.get_or_create_settings(chat_id)
        if not settings.enabled:
            return None

        flagged = detection_status != "clean" or risk_score > 0
        should_store_text = (
            settings.capture_mode == CAPTURE_FULL_TEXT
            or (settings.capture_mode == CAPTURE_FLAGGED_ONLY and flagged)
        )

        stmt = select(ObservedMessage).where(
            ObservedMessage.chat_id == chat_id,
            ObservedMessage.message_id == message_id,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        values: dict[str, Any] = {
            "sender_id": sender_id,
            "sender_username": sender_username,
            "sender_first_name": sender_first_name,
            "sender_last_name": sender_last_name,
            "sender_is_bot": sender_is_bot,
            "sender_chat_id": sender_chat_id,
            "message_type": message_type,
            "text_hash": _hash_text(text),
            "text": text if should_store_text else None,
            "text_stored": should_store_text,
            "has_text": bool(text),
            "is_edited": is_edited,
            "is_forwarded": is_forwarded,
            "forward_from_chat_id": forward_from_chat_id,
            "reply_to_message_id": reply_to_message_id,
            "entities": entities,
            "detection_status": detection_status,
            "risk_score": risk_score,
            "ad_score": ad_score,
            "security_score": security_score,
            "ai_score": ai_score,
            "detection_result": detection_result,
            "message_date": message_date,
            "updated_at": now,
        }

        if existing is not None:
            for key, value in values.items():
                setattr(existing, key, value)
            await self._session.flush()
            return existing

        message = ObservedMessage(
            chat_id=chat_id,
            message_id=message_id,
            **values,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def link_event(
        self,
        chat_id: int,
        message_id: int,
        event_id: uuid.UUID,
        detection_status: str,
    ) -> None:
        stmt = select(ObservedMessage).where(
            ObservedMessage.chat_id == chat_id,
            ObservedMessage.message_id == message_id,
        )
        result = await self._session.execute(stmt)
        message = result.scalar_one_or_none()
        if message is None:
            return
        message.event_id = event_id
        message.detection_status = detection_status
        message.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def list_messages(
        self,
        limit: int = 100,
        offset: int = 0,
        chat_id: int | None = None,
        sender_id: int | None = None,
        flagged_only: bool = False,
    ) -> list[ObservedMessage]:
        conditions = []
        if chat_id is not None:
            conditions.append(ObservedMessage.chat_id == chat_id)
        if sender_id is not None:
            conditions.append(ObservedMessage.sender_id == sender_id)
        if flagged_only:
            conditions.append(ObservedMessage.detection_status != "clean")
        stmt = (
            select(ObservedMessage)
            .where(and_(*conditions) if conditions else True)
            .order_by(ObservedMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_messages(
        self,
        chat_id: int | None = None,
        sender_id: int | None = None,
        flagged_only: bool = False,
    ) -> int:
        conditions = []
        if chat_id is not None:
            conditions.append(ObservedMessage.chat_id == chat_id)
        if sender_id is not None:
            conditions.append(ObservedMessage.sender_id == sender_id)
        if flagged_only:
            conditions.append(ObservedMessage.detection_status != "clean")
        stmt = select(func.count()).select_from(ObservedMessage).where(
            and_(*conditions) if conditions else True
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_message(self, chat_id: int, message_id: int) -> ObservedMessage | None:
        stmt = select(ObservedMessage).where(
            ObservedMessage.chat_id == chat_id,
            ObservedMessage.message_id == message_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def retention_stats(self, chat_id: int) -> dict:
        settings = await self.get_or_create_settings(chat_id)
        total = await self.count_messages(chat_id=chat_id)
        flagged = await self.count_messages(chat_id=chat_id, flagged_only=True)
        text_stmt = select(func.count()).select_from(ObservedMessage).where(
            ObservedMessage.chat_id == chat_id,
            ObservedMessage.text_stored.is_(True),
        )
        text_result = await self._session.execute(text_stmt)
        return {
            "total_messages": total,
            "flagged_messages": flagged,
            "stored_text_messages": int(text_result.scalar_one()),
            "metadata_retention_days": settings.metadata_retention_days,
            "flagged_retention_days": settings.flagged_retention_days,
        }

    async def apply_retention(self) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        settings_result = await self._session.execute(select(GroupCaptureSetting))
        redacted_text = 0
        deleted_metadata = 0

        for settings in settings_result.scalars().all():
            clean_text_cutoff = now - timedelta(days=settings.metadata_retention_days)
            flagged_text_cutoff = now - timedelta(days=settings.flagged_retention_days)

            clean_stmt = select(ObservedMessage).where(
                ObservedMessage.chat_id == settings.chat_id,
                ObservedMessage.detection_status == "clean",
                ObservedMessage.text_stored.is_(True),
                ObservedMessage.created_at < clean_text_cutoff,
            )
            flagged_stmt = select(ObservedMessage).where(
                ObservedMessage.chat_id == settings.chat_id,
                ObservedMessage.detection_status != "clean",
                ObservedMessage.text_stored.is_(True),
                ObservedMessage.created_at < flagged_text_cutoff,
            )
            for stmt in (clean_stmt, flagged_stmt):
                result = await self._session.execute(stmt)
                for message in result.scalars().all():
                    message.text = None
                    message.text_stored = False
                    message.updated_at = now
                    redacted_text += 1

            metadata_cutoff = now - timedelta(days=max(settings.metadata_retention_days * 3, settings.flagged_retention_days * 2))
            delete_stmt = delete(ObservedMessage).where(
                ObservedMessage.chat_id == settings.chat_id,
                ObservedMessage.text_stored.is_(False),
                ObservedMessage.created_at < metadata_cutoff,
            )
            delete_result = await self._session.execute(delete_stmt)
            deleted_metadata += delete_result.rowcount or 0

        await self._session.flush()
        return {"redacted_text": redacted_text, "deleted_metadata": deleted_metadata}
