from __future__ import annotations

import uuid

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AllowedEntity


class AllowlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        chat_id: uuid.UUID,
        entity_type: str,
        entity_value: str,
        telegram_entity_id: int | None = None,
        display_name: str | None = None,
        created_by_user_id: int | None = None,
    ) -> AllowedEntity:
        entity = AllowedEntity(
            chat_id=chat_id,
            entity_type=entity_type,
            entity_value=entity_value.lower(),
            telegram_entity_id=telegram_entity_id,
            display_name=display_name,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def remove(self, chat_id: uuid.UUID, entity_type: str, entity_value: str) -> bool:
        stmt = delete(AllowedEntity).where(
            and_(
                AllowedEntity.chat_id == chat_id,
                AllowedEntity.entity_type == entity_type,
                AllowedEntity.entity_value == entity_value.lower(),
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def exists(self, chat_id: uuid.UUID, entity_type: str, entity_value: str) -> bool:
        stmt = select(AllowedEntity).where(
            and_(
                AllowedEntity.chat_id == chat_id,
                AllowedEntity.entity_type == entity_type,
                AllowedEntity.entity_value == entity_value.lower(),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_all_for_chat(self, chat_id: uuid.UUID) -> list[AllowedEntity]:
        stmt = (
            select(AllowedEntity)
            .where(AllowedEntity.chat_id == chat_id)
            .order_by(AllowedEntity.entity_type, AllowedEntity.entity_value)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(self, chat_id: uuid.UUID, entity_type: str) -> list[AllowedEntity]:
        stmt = select(AllowedEntity).where(
            and_(
                AllowedEntity.chat_id == chat_id,
                AllowedEntity.entity_type == entity_type,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def remove_by_telegram_id(self, chat_id: uuid.UUID, telegram_entity_id: int) -> bool:
        stmt = delete(AllowedEntity).where(
            and_(
                AllowedEntity.chat_id == chat_id,
                AllowedEntity.telegram_entity_id == telegram_entity_id,
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
