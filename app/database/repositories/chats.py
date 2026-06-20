from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Chat


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_chat_id: int) -> Chat | None:
        stmt = select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_chat_id: int,
        title: str | None = None,
        username: str | None = None,
        owner_user_id: int | None = None,
        linked_chat_id: int | None = None,
    ) -> Chat:
        chat = Chat(
            telegram_chat_id=telegram_chat_id,
            title=title,
            username=username,
            owner_user_id=owner_user_id,
            linked_chat_id=linked_chat_id,
        )
        self._session.add(chat)
        await self._session.flush()
        return chat

    async def update_mode(self, telegram_chat_id: int, mode: str) -> Chat | None:
        chat = await self.get_by_telegram_id(telegram_chat_id)
        if chat is None:
            return None
        chat.mode = mode
        chat.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return chat

    async def set_enabled(self, telegram_chat_id: int, enabled: bool) -> Chat | None:
        chat = await self.get_by_telegram_id(telegram_chat_id)
        if chat is None:
            return None
        chat.enabled = enabled
        chat.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return chat

    async def set_bot_permission(self, telegram_chat_id: int, can_delete: bool) -> Chat | None:
        chat = await self.get_by_telegram_id(telegram_chat_id)
        if chat is None:
            return None
        chat.bot_can_delete_messages = can_delete
        chat.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return chat

    async def mark_removed(self, telegram_chat_id: int) -> Chat | None:
        chat = await self.get_by_telegram_id(telegram_chat_id)
        if chat is None:
            return None
        chat.enabled = False
        chat.removed_at = datetime.now(timezone.utc)
        chat.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return chat

    async def delete_chat_data(self, telegram_chat_id: int) -> None:
        chat = await self.get_by_telegram_id(telegram_chat_id)
        if chat is not None:
            await self._session.delete(chat)
            await self._session.flush()

    async def get_all_active(self) -> list[Chat]:
        stmt = select(Chat).where(
            Chat.enabled == True,  # noqa: E712
            Chat.removed_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_active(self) -> int:
        stmt = select(Chat).where(
            Chat.enabled == True,  # noqa: E712
            Chat.removed_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())
