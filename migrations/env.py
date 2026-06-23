import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.base import Base
from app.database.models import Chat, AllowedEntity, DeletionLog  # noqa: F401
from app.database.secadmin_base import SecAdminBase
from app.database.secadmin_models import (  # noqa: F401
    AiAnalysisJob,
    AiFeedback,
    AiMessageAnalysis,
    AiModelRegistry,
    Case,
    CaseEvent,
    CaseNote,
    EnforcementAction,
    EventIndicator,
    GroupCaptureSetting,
    Indicator,
    MemberRiskSignal,
    MessageEmbedding,
    ObservedMessage,
    ObservedUser,
    Officer,
    OfficerAuditLog,
    OfficerSession,
    SecurityEvent,
    SecurityObservationOutbox,
    SystemHealthEvent,
    TelegramQueryRequest,
    UserChatProfile,
    UserObservedName,
)

config = context.config
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [Base.metadata, SecAdminBase.metadata]


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
