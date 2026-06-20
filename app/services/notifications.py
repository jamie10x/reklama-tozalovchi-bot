import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


async def notify_admins(
    bot: Bot,
    chat_id: int,
    message: str,
) -> None:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                try:
                    await bot.send_message(admin.user.id, message)
                except Exception:
                    logger.debug("Could not send notification to admin %d", admin.user.id)
    except Exception as e:
        logger.warning("Failed to notify admins in chat %d: %s", chat_id, e)
