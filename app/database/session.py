from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.database.base import Base
from app.database.secadmin_base import SecAdminBase

_engine = None
_sessionmaker = None
_secadmin_engine = None
_secadmin_sessionmaker = None


async def init_db(settings: Settings) -> None:
    global _engine, _sessionmaker
    _engine = create_async_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )
    _sessionmaker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def init_secadmin_db(settings: Settings) -> None:
    global _secadmin_engine, _secadmin_sessionmaker
    _secadmin_engine = create_async_engine(
        settings.secadmin_database_url,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,
        echo=False,
    )
    _secadmin_sessionmaker = async_sessionmaker(
        _secadmin_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    global _engine, _sessionmaker, _secadmin_engine, _secadmin_sessionmaker
    if _engine is not None:
        await _engine.dispose()
    if _secadmin_engine is not None:
        await _secadmin_engine.dispose()
    _engine = None
    _sessionmaker = None
    _secadmin_engine = None
    _secadmin_sessionmaker = None


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return _sessionmaker


def get_secadmin_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _secadmin_sessionmaker is None:
        raise RuntimeError("SecAdmin database not initialized. Call init_secadmin_db first.")
    return _secadmin_sessionmaker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_secadmin_session() -> AsyncGenerator[AsyncSession, None]:
    sm = get_secadmin_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    if _engine is None:
        raise RuntimeError("Database not initialized.")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_all_secadmin_tables() -> None:
    if _secadmin_engine is None:
        raise RuntimeError("SecAdmin database not initialized.")
    async with _secadmin_engine.begin() as conn:
        await conn.run_sync(SecAdminBase.metadata.create_all)
