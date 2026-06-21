import uuid
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.database.models import Chat

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_adcleaner.db"


@pytest_asyncio.fixture(loop_scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def sample_chat(session):
    chat = Chat(
        id=uuid.uuid4(),
        telegram_chat_id=-1001234567890,
        title="Test Group",
        username="test_group",
        enabled=True,
        mode="normal",
        owner_user_id=12345,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(chat)
    await session.flush()
    return chat
