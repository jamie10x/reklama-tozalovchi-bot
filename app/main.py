import asyncio
import contextlib

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.commands import set_bot_commands
from app.bot.middlewares import DatabaseSessionMiddleware, ErrorLoggingMiddleware, I18nMiddleware
from app.config import load_config
from app.core.logging import get_logger, setup_logging
from app.database.session import close_db, get_session, init_db, init_secadmin_db
from app.handlers import commands, edited_messages, members, membership, messages, private
from app.secadmin.worker import SecAdminWorker
from app.services.cleanup import start_cleanup_task
from app.services.enforcement_bridge import EnforcementBridge

logger = get_logger(__name__)


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level, config.log_format)

    logger.info("Initializing database...")
    await init_db(config)

    secadmin_available = False
    try:
        await init_secadmin_db(config)
        logger.info("SecAdmin database initialized.")
        secadmin_available = True
    except Exception:
        logger.warning("SecAdmin database not available; running without observation.")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )

    dp = Dispatcher()

    dp.include_router(private.router)
    dp.include_router(membership.router)
    dp.include_router(members.router)
    dp.include_router(commands.router)
    dp.include_router(messages.router)
    dp.include_router(edited_messages.router)

    dp.update.middleware(ErrorLoggingMiddleware())
    dp.update.middleware(DatabaseSessionMiddleware())
    dp.update.middleware(I18nMiddleware(config.bot_language))

    dp["settings"] = config

    cleanup_task = start_cleanup_task(config.cleanup_interval_minutes)

    secadmin_worker = SecAdminWorker() if secadmin_available else None
    if secadmin_worker is not None:
        secadmin_worker.start()

    enforcement_bridge = EnforcementBridge(bot) if secadmin_available else None
    if enforcement_bridge is not None:
        enforcement_bridge.start()

    await set_bot_commands(bot)

    async with get_session() as session:
        from app.services.permissions import refresh_all_bot_permissions

        await refresh_all_bot_permissions(bot, session)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        if secadmin_worker is not None:
            await secadmin_worker.stop()
        if enforcement_bridge is not None:
            await enforcement_bridge.stop()
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        await bot.session.close()
        await close_db()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
