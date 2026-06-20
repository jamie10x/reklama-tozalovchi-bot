import logging

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.chats import ChatRepository

logger = logging.getLogger(__name__)


async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        result = isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
        logger.info(
            "Admin check: user=%d chat=%d member_type=%s is_admin=%s",
            user_id,
            chat_id,
            type(member).__name__,
            result,
        )
        return result
    except Exception as e:
        logger.warning(
            "Admin check failed (exception): user=%d chat=%d error=%s",
            user_id,
            chat_id,
            e,
        )
        return False


async def bot_can_delete_messages(bot: Bot, chat_id: int, chat_title: str | None = None) -> bool:
    ctx = f"chat_id={chat_id}" + (f" title={chat_title!r}" if chat_title else "")
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if isinstance(bot_member, ChatMemberOwner):
            logger.info("Bot is chat owner in %s — can_delete=True", ctx)
            return True
        if isinstance(bot_member, ChatMemberAdministrator):
            can = bot_member.can_delete_messages or False
            logger.info(
                "Bot is admin in %s can_delete_messages=%s",
                ctx,
                can,
            )
            return can
        logger.info("Bot is not admin in %s status=%s", ctx, type(bot_member).__name__)
        return False
    except Exception as e:
        logger.warning("Failed to check bot permissions in %s error=%s", ctx, e)
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
                "Refreshed permission: chat_id=%d title=%r can_delete=%s (was %s)",
                chat.telegram_chat_id,
                chat.title,
                can_delete,
                chat.bot_can_delete_messages,
            )
    logger.info("Permission refresh complete for %d chats", len(chats))
