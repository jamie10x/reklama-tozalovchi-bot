import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.commands import set_bot_commands
from app.bot.middlewares import DatabaseSessionMiddleware, ErrorLoggingMiddleware
from app.config import load_config
from app.database.session import close_db, init_db
from app.handlers import commands, edited_messages, membership, messages, private
from app.logging_config import setup_logging
from app.services.cleanup import start_cleanup_task

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level)

    logger.info("Initializing database...")
    await init_db(config)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        ),
    )

    dp = Dispatcher()

    dp.include_router(private.router)
    dp.include_router(membership.router)
    dp.include_router(commands.router)
    dp.include_router(messages.router)
    dp.include_router(edited_messages.router)

    dp.update.middleware(ErrorLoggingMiddleware())
    dp.update.middleware(DatabaseSessionMiddleware())

    dp["settings"] = config

    cleanup_task = start_cleanup_task(config.cleanup_interval_minutes)

    await set_bot_commands(bot)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        await bot.session.close()
        await close_db()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
