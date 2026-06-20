from __future__ import annotations

import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.allowlist import AllowlistRepository
from app.database.repositories.chats import ChatRepository
from app.database.repositories.deletion_logs import DeletionLogRepository
from app.detector.service import DetectionService
from app.services.permissions import is_user_admin

logger = logging.getLogger(__name__)


class ModerationService:
    def __init__(
        self,
        session: AsyncSession,
        bot: Bot,
        detection_service: DetectionService | None = None,
    ) -> None:
        self._session = session
        self._bot = bot
        self._chat_repo = ChatRepository(session)
        self._log_repo = DeletionLogRepository(session)
        self._allowlist_repo = AllowlistRepository(session)
        self._detection = detection_service or DetectionService()

    async def process_message(
        self,
        chat_id: int,
        message_id: int,
        text: str | None,
        sender_id: int | None,
        sender_is_bot: bool = False,
        sender_chat_id: int | None = None,
        is_forwarded: bool = False,
        forward_from_chat_id: int | None = None,
        entities: list | None = None,
        caption_entities: list | None = None,
    ) -> bool:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None or not chat.enabled:
            return False

        if not chat.bot_can_delete_messages:
            logger.warning(
                "Bot cannot delete messages in chat %d — skipping detection",
                chat_id,
            )
            return False

        if sender_id is not None:
            is_admin = await is_user_admin(self._bot, chat_id, sender_id)
            if is_admin:
                return False

        if sender_id is not None:
            user_allowlist = await self._allowlist_repo.get_by_type(chat.id, "user")
            for entry in user_allowlist:
                if entry.telegram_entity_id == sender_id:
                    return False
                if entry.entity_value == str(sender_id):
                    return False

        if sender_is_bot and sender_id is not None:
            bot_allowlist = await self._allowlist_repo.get_by_type(chat.id, "bot")
            for entry in bot_allowlist:
                if entry.telegram_entity_id == sender_id:
                    return False

        result = await self._detection.analyze(
            text=text or "",
            entities=entities or [],
            caption_entities=caption_entities or [],
            is_forwarded=is_forwarded,
            forward_from_chat_id=forward_from_chat_id,
            linked_chat_id=chat.linked_chat_id,
            chat_telegram_id=chat_id,
            allowlist_repo=self._allowlist_repo,
            chat_uuid=chat.id,
        )

        if not result.is_advertisement:
            return False

        try:
            await self._bot.delete_message(chat_id, message_id)
            logger.info(
                "Deleted message %d in chat %d (score=%d reasons=%s)",
                message_id,
                chat_id,
                result.score,
                result.reasons,
            )
        except Exception as e:
            logger.warning("Failed to delete message %d in chat %d: %s", message_id, chat_id, e)
            return False

        excerpt = (text or "")[:250] if text else None

        await self._log_repo.create(
            chat_id=chat.id,
            telegram_message_id=message_id,
            score=result.score,
            reasons=result.reasons,
            detected_domains=result.detected_domains,
            detected_telegram_entities=result.detected_telegram_entities,
            message_excerpt=excerpt,
            sender_user_id=sender_id,
            sender_chat_id=sender_chat_id,
            sender_is_bot=sender_is_bot,
        )

        return True
