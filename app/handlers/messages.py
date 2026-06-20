from __future__ import annotations

import logging

from aiogram import Router, types
from aiogram.enums import ChatType
from aiogram.types import MessageOriginChannel, MessageOriginChat, MessageOriginUser

from app.bot.filters import IsGroupMessage
from app.database.repositories.chats import ChatRepository
from app.services.moderation import ModerationService

logger = logging.getLogger(__name__)

router = Router()


def _extract_forward_chat_id(message: types.Message) -> tuple[int | None, bool]:
    origin = getattr(message, "forward_origin", None)
    if origin is None:
        return None, False
    if isinstance(origin, (MessageOriginChannel, MessageOriginChat)):
        return origin.chat.id, True
    if isinstance(origin, MessageOriginUser):
        return None, True
    return None, True


@router.message(IsGroupMessage())
async def handle_group_message(message: types.Message, session=None) -> None:
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    chat_repo = ChatRepository(session)
    chat = await chat_repo.get_by_telegram_id(message.chat.id)
    if chat is None or not chat.enabled:
        return

    text = message.text or message.caption or ""

    forward_from_chat_id, is_forwarded = _extract_forward_chat_id(message)

    mod_service = ModerationService(
        session=session,
        bot=message.bot,
    )

    await mod_service.process_message(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=text,
        sender_id=message.from_user.id if message.from_user else None,
        sender_is_bot=message.from_user.is_bot if message.from_user else False,
        sender_chat_id=message.sender_chat.id if message.sender_chat else None,
        is_forwarded=is_forwarded,
        forward_from_chat_id=forward_from_chat_id,
        entities=message.entities or message.caption_entities or [],
        caption_entities=message.caption_entities or [],
    )
