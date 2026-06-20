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
        logger.debug(
            "Admin check for user %d in chat %d: status=%s result=%s",
            user_id,
            chat_id,
            type(member).__name__,
            result,
        )
        return result
    except Exception as e:
        logger.warning(
            "Failed to check admin status for user %d in chat %d: %s",
            user_id,
            chat_id,
            e,
        )
        return False


async def bot_can_delete_messages(bot: Bot, chat_id: int) -> bool:
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if isinstance(bot_member, ChatMemberOwner):
            logger.debug("Bot is chat owner in %d — can delete", chat_id)
            return True
        if isinstance(bot_member, ChatMemberAdministrator):
            can = bot_member.can_delete_messages or False
            logger.debug(
                "Bot is admin in %d: can_delete_messages=%s",
                chat_id,
                can,
            )
            return can
        logger.warning(
            "Bot is not admin in chat %d (status=%s)",
            chat_id,
            type(bot_member).__name__,
        )
        return False
    except Exception as e:
        logger.warning("Failed to check bot permissions in chat %d: %s", chat_id, e)
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
        can_delete = await bot_can_delete_messages(bot, chat.telegram_chat_id)
        if can_delete != chat.bot_can_delete_messages:
            await repo.set_bot_permission(chat.telegram_chat_id, can_delete)
            logger.info(
                "Refreshed permission for chat %d: can_delete=%s (was %s)",
                chat.telegram_chat_id,
                can_delete,
                chat.bot_can_delete_messages,
            )
    logger.info("Permission refresh complete for %d chats", len(chats))
