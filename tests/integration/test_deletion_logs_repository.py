from datetime import datetime, timedelta, timezone

import pytest

from app.database.repositories.deletion_logs import DeletionLogRepository


@pytest.mark.asyncio
async def test_create_deletion_log(sample_chat, session):
    repo = DeletionLogRepository(session)
    log = await repo.create(
        chat_id=sample_chat.id,
        telegram_message_id=12345,
        score=8,
        reasons=["external_url", "strong_ad_phrase"],
        detected_domains=["example.com"],
        message_excerpt="Buy now! example.com",
        sender_user_id=999,
    )
    assert log is not None
    assert log.score == 8
    assert "external_url" in (log.reasons or [])


@pytest.mark.asyncio
async def test_get_recent_logs(sample_chat, session):
    repo = DeletionLogRepository(session)
    await repo.create(
        chat_id=sample_chat.id,
        telegram_message_id=1,
        score=5,
        reasons=["test"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    await repo.create(
        chat_id=sample_chat.id,
        telegram_message_id=2,
        score=6,
        reasons=["test"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    logs = await repo.get_recent(sample_chat.id, limit=5)
    assert len(logs) == 2


@pytest.mark.asyncio
async def test_count_today(sample_chat, session):
    repo = DeletionLogRepository(session)
    await repo.create(
        chat_id=sample_chat.id,
        telegram_message_id=100,
        score=7,
        reasons=["test"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    count = await repo.count_today(sample_chat.id)
    assert count >= 1


@pytest.mark.asyncio
async def test_delete_expired_logs(sample_chat, session):
    repo = DeletionLogRepository(session)
    await repo.create(
        chat_id=sample_chat.id,
        telegram_message_id=200,
        score=5,
        reasons=["test"],
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    await repo.create(
        chat_id=sample_chat.id,
        telegram_message_id=201,
        score=6,
        reasons=["test"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    deleted = await repo.delete_expired()
    assert deleted >= 1
