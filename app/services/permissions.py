import logging

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

logger = logging.getLogger(__name__)


async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
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
            return True
        if isinstance(bot_member, ChatMemberAdministrator):
            return bot_member.can_delete_messages or False
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
