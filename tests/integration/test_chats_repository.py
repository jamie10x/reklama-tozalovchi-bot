from datetime import datetime, timezone

import pytest

from app.database.repositories.chats import ChatRepository


@pytest.mark.asyncio
async def test_create_chat(session):
    repo = ChatRepository(session)
    chat = await repo.create(
        telegram_chat_id=-1001111111111,
        title="New Group",
        username="new_group",
        owner_user_id=67890,
    )
    assert chat is not None
    assert chat.telegram_chat_id == -1001111111111
    assert chat.title == "New Group"
    assert chat.enabled is True
    assert chat.mode == "normal"


@pytest.mark.asyncio
async def test_get_chat_by_telegram_id(sample_chat, session):
    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(-1001234567890)
    assert chat is not None
    assert chat.title == "Test Group"


@pytest.mark.asyncio
async def test_get_chat_not_found(session):
    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(-1009999999999)
    assert chat is None


@pytest.mark.asyncio
async def test_update_mode(sample_chat, session):
    repo = ChatRepository(session)
    chat = await repo.update_mode(-1001234567890, "strict")
    assert chat is not None
    assert chat.mode == "strict"


@pytest.mark.asyncio
async def test_set_enabled(sample_chat, session):
    repo = ChatRepository(session)
    chat = await repo.set_enabled(-1001234567890, False)
    assert chat is not None
    assert chat.enabled is False


@pytest.mark.asyncio
async def test_set_bot_permission(sample_chat, session):
    repo = ChatRepository(session)
    chat = await repo.set_bot_permission(-1001234567890, True)
    assert chat is not None
    assert chat.bot_can_delete_messages is True


@pytest.mark.asyncio
async def test_mark_removed(sample_chat, session):
    repo = ChatRepository(session)
    chat = await repo.mark_removed(-1001234567890)
    assert chat is not None
    assert chat.enabled is False
    assert chat.removed_at is not None


@pytest.mark.asyncio
async def test_delete_chat_data(sample_chat, session):
    repo = ChatRepository(session)
    await repo.delete_chat_data(-1001234567890)
    chat = await repo.get_by_telegram_id(-1001234567890)
    assert chat is None


@pytest.mark.asyncio
async def test_get_all_active(sample_chat, session):
    repo = ChatRepository(session)
    active = await repo.get_all_active()
    assert len(active) >= 1
