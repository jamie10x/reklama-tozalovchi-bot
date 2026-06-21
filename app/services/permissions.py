from __future__ import annotations

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.repositories.chats import ChatRepository

logger = get_logger(__name__)


async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        result = isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
        logger.info(
            "Admin check",
            user=user_id,
            chat=chat_id,
            member_type=type(member).__name__,
            is_admin=result,
        )
        return result
    except Exception as e:
        logger.warning(
            "Admin check exception",
            user=user_id,
            chat=chat_id,
            error=str(e),
        )
        return False


async def bot_can_delete_messages(bot: Bot, chat_id: int, chat_title: str | None = None) -> bool:
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if isinstance(bot_member, ChatMemberOwner):
            return True
        if isinstance(bot_member, ChatMemberAdministrator):
            can = bot_member.can_delete_messages or False
            return can
        return False
    except Exception as e:
        ctx = f"chat_id={chat_id}" + (f" title={chat_title!r}" if chat_title else "")
        logger.warning("Permission check failed", chat_context=ctx, error=str(e))
        return False


async def is_group_owner(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(member, ChatMemberOwner)
    except Exception:
        return False


async def refresh_all_bot_permissions(bot: Bot, session: AsyncSession) -> None:
    repo = ChatRepository(session)
    chats = await repo.get_all_active()
    if not chats:
        logger.info("No active chats to refresh permissions for")
        return
    for chat in chats:
        can_delete = await bot_can_delete_messages(bot, chat.telegram_chat_id, chat.title)
        if can_delete != chat.bot_can_delete_messages:
            await repo.set_bot_permission(chat.telegram_chat_id, can_delete)
            logger.info(
                "Permission refreshed",
                chat_id=chat.telegram_chat_id,
                title=chat.title,
                can_delete=can_delete,
                was=chat.bot_can_delete_messages,
            )
    logger.info("Permission refresh complete for %d chats", len(chats))
