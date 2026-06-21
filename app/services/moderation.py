from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import AIService
from app.core.logging import get_logger
from app.database.repositories.allowlist import AllowlistRepository
from app.database.repositories.chats import ChatRepository
from app.database.repositories.deletion_logs import DeletionLogRepository
from app.detector.models import DetectionResult, SecurityResult
from app.detector.security import SecurityDetector
from app.detector.service import DetectionService
from app.services.observation import MessageContext, ObservationProducer
from app.services.permissions import bot_can_delete_messages as _bot_can_delete
from app.services.permissions import is_user_admin

logger = get_logger(__name__)


class ModerationService:
    def __init__(
        self,
        session: AsyncSession,
        bot: Bot,
        detection_service: DetectionService | None = None,
        security_detector: SecurityDetector | None = None,
        secadmin_session: AsyncSession | None = None,
        ai_service: AIService | None = None,
    ) -> None:
        self._session = session
        self._bot = bot
        self._chat_repo = ChatRepository(session)
        self._log_repo = DeletionLogRepository(session)
        self._allowlist_repo = AllowlistRepository(session)
        self._detection = detection_service or DetectionService()
        self._security = security_detector or SecurityDetector()
        self._secadmin_session = secadmin_session
        self._ai = ai_service

    def _make_observation_producer(self) -> ObservationProducer | None:
        if self._secadmin_session is not None:
            return ObservationProducer(self._secadmin_session)
        return None

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
        update_id: int | None = None,
    ) -> bool:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None or not chat.enabled:
            return False

        if not chat.bot_can_delete_messages:
            can_delete = await _bot_can_delete(self._bot, chat_id, chat.title)
            if can_delete:
                await self._chat_repo.set_bot_permission(chat_id, True)
                logger.info(
                    "Permission regranted",
                    chat_id=chat_id,
                    title=chat.title,
                )
            else:
                logger.warning(
                    "Cannot delete messages",
                    chat_id=chat_id,
                    title=chat.title,
                )
                return False

        if sender_id is not None:
            is_admin = await is_user_admin(self._bot, chat_id, sender_id)
            if is_admin:
                await self._produce_observation_if_needed(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text or "",
                    sender_id=sender_id,
                    sender_is_bot=sender_is_bot,
                    sender_chat_id=sender_chat_id,
                    is_forwarded=is_forwarded,
                    forward_from_chat_id=forward_from_chat_id,
                    entities=entities,
                    caption_entities=caption_entities,
                    update_id=update_id,
                )
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

        ad_result = await self._detection.analyze(
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

        security_result = self._security.analyze(text or "")

        ai_result = None
        if self._ai is not None and self._ai.enabled:
            ai_response = await self._ai.analyze_message(
                text=text or "",
                rule_result=ad_result,
            )
            if ai_response is not None:
                ai_result = ai_response.to_dict()

        await self._produce_observation_if_needed(
            chat_id=chat_id,
            message_id=message_id,
            text=text or "",
            sender_id=sender_id,
            sender_is_bot=sender_is_bot,
            sender_chat_id=sender_chat_id,
            is_forwarded=is_forwarded,
            forward_from_chat_id=forward_from_chat_id,
            entities=entities,
            caption_entities=caption_entities,
            update_id=update_id,
            ad_result=ad_result,
            security_result=security_result,
            ai_result=ai_result,
        )

        if not ad_result.is_advertisement:
            return False

        try:
            await self._bot.delete_message(chat_id, message_id)
            logger.info(
                "Deleted",
                msg_id=message_id,
                chat_id=chat_id,
                title=chat.title,
                score=ad_result.score,
                reasons=ad_result.reasons,
            )
        except Exception as e:
            logger.warning(
                "Delete failed",
                msg_id=message_id,
                chat_id=chat_id,
                error=str(e),
            )
            return False

        excerpt = (text or "")[:250] if text else None

        await self._log_repo.create(
            chat_id=chat.id,
            telegram_message_id=message_id,
            score=ad_result.score,
            reasons=ad_result.reasons,
            detected_domains=ad_result.detected_domains,
            detected_telegram_entities=ad_result.detected_telegram_entities,
            message_excerpt=excerpt,
            sender_user_id=sender_id,
            sender_chat_id=sender_chat_id,
            sender_is_bot=sender_is_bot,
        )

        return True

    async def _produce_observation_if_needed(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        sender_id: int | None = None,
        sender_is_bot: bool = False,
        sender_chat_id: int | None = None,
        is_forwarded: bool = False,
        forward_from_chat_id: int | None = None,
        entities: list | None = None,
        caption_entities: list | None = None,
        update_id: int | None = None,
        ad_result: DetectionResult | None = None,
        security_result: SecurityResult | None = None,
        ai_result: dict | None = None,
    ) -> None:
        producer = self._make_observation_producer()
        if producer is None:
            return

        ctx = MessageContext(
            chat_id=chat_id,
            message_id=message_id,
            update_id=update_id or 0,
            text=text,
            sender_id=sender_id,
            sender_is_bot=sender_is_bot,
            sender_chat_id=sender_chat_id,
            is_forwarded=is_forwarded,
            forward_from_chat_id=forward_from_chat_id,
            ad_result=ad_result,
            security_result=security_result,
            ai_result=ai_result,
            entities=entities or [],
            caption_entities=caption_entities or [],
        )

        try:
            await producer.produce(ctx)
        except Exception as e:
            logger.warning("Observation produce failed", error=str(e))
