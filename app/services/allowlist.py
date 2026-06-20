from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.allowlist import AllowlistRepository
from app.database.repositories.chats import ChatRepository


@dataclass
class AllowlistAddResult:
    success: bool
    message: str


DOMAIN_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$",
    re.IGNORECASE,
)
USERNAME_PATTERN = re.compile(r"^@?[a-z][a-z0-9_]{4,31}$", re.IGNORECASE)


def normalize_username(value: str) -> str:
    return value.lstrip("@").lower()


def normalize_domain(value: str) -> str:
    value = value.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    slash_pos = value.find("/")
    if slash_pos != -1:
        value = value[:slash_pos]
    return value


class AllowlistService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AllowlistRepository(session)
        self._chat_repo = ChatRepository(session)

    async def add_user(self, chat_id: int, username: str, created_by: int) -> AllowlistAddResult:
        normalized = normalize_username(username)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        if await self._repo.exists(chat.id, "user", normalized):
            return AllowlistAddResult(False, f"@{normalized} is already allowed.")
        await self._repo.add(
            chat_id=chat.id,
            entity_type="user",
            entity_value=normalized,
            display_name=f"@{normalized}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, f"@{normalized} has been allowed.")

    async def add_user_by_id(
        self,
        chat_id: int,
        telegram_user_id: int,
        display_name: str,
        created_by: int,
    ) -> AllowlistAddResult:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        value = str(telegram_user_id)
        if await self._repo.exists(chat.id, "user", value):
            return AllowlistAddResult(False, f"User {display_name} is already allowed.")
        await self._repo.add(
            chat_id=chat.id,
            entity_type="user",
            entity_value=value,
            telegram_entity_id=telegram_user_id,
            display_name=display_name,
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, f"{display_name} has been allowed.")

    async def add_bot(self, chat_id: int, bot_username: str, created_by: int) -> AllowlistAddResult:
        normalized = normalize_username(bot_username)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        if await self._repo.exists(chat.id, "bot", normalized):
            return AllowlistAddResult(False, f"@{normalized} is already allowed.")
        await self._repo.add(
            chat_id=chat.id,
            entity_type="bot",
            entity_value=normalized,
            display_name=f"@{normalized}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, f"@{normalized} has been allowed.")

    async def add_bot_by_id(
        self,
        chat_id: int,
        bot_user_id: int,
        bot_username: str | None,
        created_by: int,
    ) -> AllowlistAddResult:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        value = str(bot_user_id) if bot_username is None else normalize_username(bot_username)
        display = bot_username or f"bot_{bot_user_id}"
        if await self._repo.exists(chat.id, "bot", value):
            return AllowlistAddResult(False, f"@{display} is already allowed.")
        await self._repo.add(
            chat_id=chat.id,
            entity_type="bot",
            entity_value=value,
            telegram_entity_id=bot_user_id,
            display_name=f"@{display}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, f"@{display} has been allowed.")

    async def add_domain(self, chat_id: int, domain: str, created_by: int) -> AllowlistAddResult:
        normalized = normalize_domain(domain)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        if await self._repo.exists(chat.id, "domain", normalized):
            return AllowlistAddResult(False, f"{normalized} is already allowed.")
        await self._repo.add(
            chat_id=chat.id,
            entity_type="domain",
            entity_value=normalized,
            display_name=normalized,
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, f"{normalized} has been allowed.")

    async def add_telegram_chat(
        self, chat_id: int, tg_identifier: str, created_by: int
    ) -> AllowlistAddResult:
        normalized = normalize_username(tg_identifier)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        if await self._repo.exists(chat.id, "telegram_chat", normalized):
            return AllowlistAddResult(False, f"@{normalized} is already allowed.")
        await self._repo.add(
            chat_id=chat.id,
            entity_type="telegram_chat",
            entity_value=normalized,
            display_name=f"@{normalized}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, f"@{normalized} has been allowed.")

    async def remove(self, chat_id: int, entity_type: str, value: str) -> AllowlistAddResult:
        if entity_type in ("user", "bot", "telegram_chat"):
            normalized = normalize_username(value)
        else:
            normalized = normalize_domain(value)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, "Chat not found.")
        removed = await self._repo.remove(chat.id, entity_type, normalized)
        if removed:
            return AllowlistAddResult(True, f"{value} has been removed from the allowlist.")
        return AllowlistAddResult(False, f"{value} was not found in the allowlist.")

    async def get_formatted_list(self, chat_id: int) -> str:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return "Chat not found."
        entities = await self._repo.get_all_for_chat(chat.id)
        if not entities:
            return "No allowed entities configured."

        icon_map = {
            "user": "👤",
            "bot": "🤖",
            "telegram_chat": "💬",
            "domain": "🌐",
        }
        lines = ["<b>Allowed entities:</b>\n"]
        for e in entities:
            icon = icon_map.get(e.entity_type, "•")
            name = e.display_name or e.entity_value
            lines.append(f"{icon} <b>{e.entity_type.capitalize()}:</b> {name}")
        return "\n".join(lines)
