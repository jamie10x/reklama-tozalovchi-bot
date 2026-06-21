from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.allowlist import AllowlistRepository
from app.database.repositories.chats import ChatRepository
from app.i18n import I18n


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
    def __init__(self, session: AsyncSession, i18n: I18n | None = None) -> None:
        self._session = session
        self._repo = AllowlistRepository(session)
        self._chat_repo = ChatRepository(session)
        self._i18n = i18n or I18n()

    def _t(self, key: str, **kwargs: str) -> str:
        return self._i18n.t(f"allowlist.{key}", **kwargs)

    async def add_user(self, chat_id: int, username: str, created_by: int) -> AllowlistAddResult:
        normalized = normalize_username(username)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        if await self._repo.exists(chat.id, "user", normalized):
            return AllowlistAddResult(False, self._t("already_exists", entity=f"@{normalized}"))
        await self._repo.add(
            chat_id=chat.id,
            entity_type="user",
            entity_value=normalized,
            display_name=f"@{normalized}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, self._t("allowed", entity=f"@{normalized}"))

    async def add_user_by_id(
        self,
        chat_id: int,
        telegram_user_id: int,
        display_name: str,
        created_by: int,
    ) -> AllowlistAddResult:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        value = str(telegram_user_id)
        if await self._repo.exists(chat.id, "user", value):
            return AllowlistAddResult(False, self._t("already_exists", entity=display_name))
        await self._repo.add(
            chat_id=chat.id,
            entity_type="user",
            entity_value=value,
            telegram_entity_id=telegram_user_id,
            display_name=display_name,
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, self._t("allowed", entity=display_name))

    async def add_bot(self, chat_id: int, bot_username: str, created_by: int) -> AllowlistAddResult:
        normalized = normalize_username(bot_username)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        if await self._repo.exists(chat.id, "bot", normalized):
            return AllowlistAddResult(False, self._t("already_exists", entity=f"@{normalized}"))
        await self._repo.add(
            chat_id=chat.id,
            entity_type="bot",
            entity_value=normalized,
            display_name=f"@{normalized}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, self._t("allowed", entity=f"@{normalized}"))

    async def add_bot_by_id(
        self,
        chat_id: int,
        bot_user_id: int,
        bot_username: str | None,
        created_by: int,
    ) -> AllowlistAddResult:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        value = str(bot_user_id) if bot_username is None else normalize_username(bot_username)
        display = bot_username or f"bot_{bot_user_id}"
        if await self._repo.exists(chat.id, "bot", value):
            return AllowlistAddResult(False, self._t("already_exists", entity=f"@{display}"))
        await self._repo.add(
            chat_id=chat.id,
            entity_type="bot",
            entity_value=value,
            telegram_entity_id=bot_user_id,
            display_name=f"@{display}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, self._t("allowed", entity=f"@{display}"))

    async def add_domain(self, chat_id: int, domain: str, created_by: int) -> AllowlistAddResult:
        normalized = normalize_domain(domain)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        if await self._repo.exists(chat.id, "domain", normalized):
            return AllowlistAddResult(False, self._t("already_exists", entity=normalized))
        await self._repo.add(
            chat_id=chat.id,
            entity_type="domain",
            entity_value=normalized,
            display_name=normalized,
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, self._t("allowed", entity=normalized))

    async def add_telegram_chat(
        self, chat_id: int, tg_identifier: str, created_by: int
    ) -> AllowlistAddResult:
        normalized = normalize_username(tg_identifier)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        if await self._repo.exists(chat.id, "telegram_chat", normalized):
            return AllowlistAddResult(False, self._t("already_exists", entity=f"@{normalized}"))
        await self._repo.add(
            chat_id=chat.id,
            entity_type="telegram_chat",
            entity_value=normalized,
            display_name=f"@{normalized}",
            created_by_user_id=created_by,
        )
        return AllowlistAddResult(True, self._t("allowed", entity=f"@{normalized}"))

    async def remove(self, chat_id: int, entity_type: str, value: str) -> AllowlistAddResult:
        if entity_type in ("user", "bot", "telegram_chat"):
            normalized = normalize_username(value)
        else:
            normalized = normalize_domain(value)
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return AllowlistAddResult(False, self._t("chat_not_found"))
        removed = await self._repo.remove(chat.id, entity_type, normalized)
        if removed:
            return AllowlistAddResult(True, self._t("removed", entity=value))
        return AllowlistAddResult(False, self._t("not_found", entity=value))

    async def get_formatted_list(self, chat_id: int) -> str:
        chat = await self._chat_repo.get_by_telegram_id(chat_id)
        if chat is None:
            return self._t("chat_not_found")
        entities = await self._repo.get_all_for_chat(chat.id)
        if not entities:
            return self._t("empty")

        icon_map = {
            "user": "👤",
            "bot": "🤖",
            "telegram_chat": "💬",
            "domain": "🌐",
        }
        lines = [self._t("title")]
        for e in entities:
            icon = icon_map.get(e.entity_type, "•")
            type_name = self._t(f"types.{e.entity_type}", default=e.entity_type.capitalize())
            name = e.display_name or e.entity_value
            lines.append(self._t("item", icon=icon, type=type_name, name=name))
        return "\n".join(lines)
