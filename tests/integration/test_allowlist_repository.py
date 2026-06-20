import pytest

from app.database.repositories.allowlist import AllowlistRepository


@pytest.mark.asyncio
async def test_add_allowed_entity(sample_chat, session):
    repo = AllowlistRepository(session)
    entity = await repo.add(
        chat_id=sample_chat.id,
        entity_type="user",
        entity_value="@trusted_user",
        display_name="@trusted_user",
        created_by_user_id=12345,
    )
    assert entity is not None
    assert entity.entity_value == "@trusted_user"


@pytest.mark.asyncio
async def test_add_domain_entity(sample_chat, session):
    repo = AllowlistRepository(session)
    entity = await repo.add(
        chat_id=sample_chat.id,
        entity_type="domain",
        entity_value="example.com",
    )
    assert entity is not None
    assert entity.entity_type == "domain"


@pytest.mark.asyncio
async def test_duplicate_prevention(sample_chat, session):
    repo = AllowlistRepository(session)
    await repo.add(
        chat_id=sample_chat.id,
        entity_type="domain",
        entity_value="example.com",
    )
    exists = await repo.exists(sample_chat.id, "domain", "example.com")
    assert exists is True


@pytest.mark.asyncio
async def test_remove_entity(sample_chat, session):
    repo = AllowlistRepository(session)
    await repo.add(
        chat_id=sample_chat.id,
        entity_type="user",
        entity_value="@test_user",
    )
    removed = await repo.remove(sample_chat.id, "user", "@test_user")
    assert removed is True
    exists = await repo.exists(sample_chat.id, "user", "@test_user")
    assert exists is False


@pytest.mark.asyncio
async def test_remove_nonexistent(sample_chat, session):
    repo = AllowlistRepository(session)
    removed = await repo.remove(sample_chat.id, "user", "@nonexistent")
    assert removed is False


@pytest.mark.asyncio
async def test_get_all_for_chat(sample_chat, session):
    repo = AllowlistRepository(session)
    await repo.add(chat_id=sample_chat.id, entity_type="user", entity_value="@user1")
    await repo.add(chat_id=sample_chat.id, entity_type="domain", entity_value="site.com")
    entities = await repo.get_all_for_chat(sample_chat.id)
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_get_by_type(sample_chat, session):
    repo = AllowlistRepository(session)
    await repo.add(chat_id=sample_chat.id, entity_type="user", entity_value="@user1")
    await repo.add(chat_id=sample_chat.id, entity_type="domain", entity_value="site.com")
    users = await repo.get_by_type(sample_chat.id, "user")
    assert len(users) == 1
    domains = await repo.get_by_type(sample_chat.id, "domain")
    assert len(domains) == 1
