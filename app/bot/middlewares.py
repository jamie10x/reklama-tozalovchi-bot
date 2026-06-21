from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.session import get_secadmin_sessionmaker, get_sessionmaker
from app.i18n import I18n

logger = get_logger(__name__)


@asynccontextmanager
async def _maybe_secadmin_session() -> AsyncGenerator[AsyncSession | None, None]:
    try:
        sm = get_secadmin_sessionmaker()
        async with sm() as session:
            yield session
    except RuntimeError:
        yield None


class DatabaseSessionMiddleware(BaseMiddleware):
    def __init__(self, ai_service: Any = None) -> None:
        self._ai_service = ai_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        sm = get_sessionmaker()
        async with sm() as session, _maybe_secadmin_session() as secadmin_session:
            data["session"] = session
            if secadmin_session is not None:
                data["secadmin_session"] = secadmin_session
                if self._ai_service is not None:
                    data["ai_service"] = self._ai_service
            try:
                return await handler(event, data)
            except Exception:
                if secadmin_session is not None:
                    await secadmin_session.rollback()
                await session.rollback()
                raise
            else:
                if secadmin_session is not None:
                    await secadmin_session.commit()
            finally:
                data.pop("session", None)
                data.pop("secadmin_session", None)


class ErrorLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            logger.exception(
                "Unhandled error processing %s",
                type(event).__name__,
            )


class I18nMiddleware(BaseMiddleware):
    def __init__(self, locale: str = "uz") -> None:
        self._i18n = I18n(locale)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["i18n"] = self._i18n
        return await handler(event, data)
