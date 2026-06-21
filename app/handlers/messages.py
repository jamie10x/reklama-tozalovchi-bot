from __future__ import annotations

from aiogram import Router, types
from aiogram.enums import ChatType
from aiogram.types import MessageOriginChannel, MessageOriginChat, MessageOriginUser

from app.bot.filters import IsGroupMessage
from app.core.logging import get_logger
from app.database.repositories.chats import ChatRepository
from app.database.repositories.users import ObservedUserRepository
from app.services.moderation import ModerationService

logger = get_logger(__name__)

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
    if message.audio:
        return "audio"
    if message.voice:
        return "voice"
    if message.sticker:
        return "sticker"
    return "other"


async def _observe_sender(message: types.Message, repo: ObservedUserRepository) -> None:
    if message.from_user is None or message.from_user.is_bot:
        return
    user = message.from_user
    await repo.upsert(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_bot=user.is_bot or False,
        language_code=user.language_code,
        is_premium=user.is_premium or False,
    )
    await repo.upsert_profile(
        user_id=user.id,
        chat_id=message.chat.id,
        is_admin=False,
    )
    await repo.increment_message_count(user.id, message.chat.id)


@router.message(IsGroupMessage())
async def handle_group_message(
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

    if secadmin_session is not None:
        try:
            user_repo = ObservedUserRepository(secadmin_session)
            await _observe_sender(message, user_repo)
        except Exception:
            uid = message.from_user.id if message.from_user else 0
            logger.warning("Failed to observe user", user_id=uid)

    text = message.text or message.caption or ""

    forward_from_chat_id, is_forwarded = _extract_forward_chat_id(message)

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
        is_forwarded=is_forwarded,
        forward_from_chat_id=forward_from_chat_id,
        entities=message.entities or message.caption_entities or [],
        caption_entities=message.caption_entities or [],
        sender_username=message.from_user.username if message.from_user else None,
        sender_first_name=message.from_user.first_name if message.from_user else None,
        sender_last_name=message.from_user.last_name if message.from_user else None,
        message_type=_message_type(message),
        message_date=message.date,
        reply_to_message_id=message.reply_to_message.message_id
        if message.reply_to_message
        else None,
    )

    if deleted:
        logger.info(
            "Ad deleted",
            chat_id=message.chat.id,
            message_id=message.message_id,
            sender_id=message.from_user.id if message.from_user else None,
        )
