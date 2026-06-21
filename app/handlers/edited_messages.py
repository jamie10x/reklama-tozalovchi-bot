from __future__ import annotations

from aiogram import Router, types
from aiogram.enums import ChatType

from app.bot.filters import IsGroupMessage
from app.core.logging import get_logger
from app.database.repositories.chats import ChatRepository
from app.services.moderation import ModerationService

logger = get_logger(__name__)

router = Router()


def _message_type(message: types.Message) -> str:
    if message.text:
        return "text"
    if message.caption:
        return "caption"
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.document:
        return "document"
    return "other"


@router.edited_message(IsGroupMessage())
async def handle_edited_message(
    message: types.Message,
    session=None,
    secadmin_session=None,
    ai_service=None,
) -> None:
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    chat_repo = ChatRepository(session)
    chat = await chat_repo.get_by_telegram_id(message.chat.id)
    if chat is None or not chat.enabled:
        return

    text = message.text or message.caption or ""
    if not text:
        return

    mod_service = ModerationService(
        session=session,
        bot=message.bot,
        secadmin_session=secadmin_session,
        ai_service=ai_service,
    )

    deleted = await mod_service.process_message(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=text,
        sender_id=message.from_user.id if message.from_user else None,
        sender_is_bot=message.from_user.is_bot if message.from_user else False,
        sender_chat_id=message.sender_chat.id if message.sender_chat else None,
        entities=message.entities or message.caption_entities or [],
        caption_entities=message.caption_entities or [],
        sender_username=message.from_user.username if message.from_user else None,
        sender_first_name=message.from_user.first_name if message.from_user else None,
        sender_last_name=message.from_user.last_name if message.from_user else None,
        message_type=_message_type(message),
        message_date=message.date,
        is_edited=True,
        reply_to_message_id=message.reply_to_message.message_id
        if message.reply_to_message
        else None,
    )

    if deleted:
        logger.info(
            "Ad deleted (edited)",
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
