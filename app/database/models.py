import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_chat_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    owner_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    linked_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    bot_can_delete_messages: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            mode.in_(["relaxed", "normal", "strict"]),
            name="ck_chat_mode",
        ),
    )

    allowed_entities: Mapped[list["AllowedEntity"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )
    deletion_logs: Mapped[list["DeletionLog"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class AllowedEntity(Base):
    __tablename__ = "allowed_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_value: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_entity_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            entity_type.in_(["user", "bot", "telegram_chat", "domain"]),
            name="ck_allowed_entity_type",
        ),
    )

    chat: Mapped["Chat"] = relationship(back_populates="allowed_entities")


class DeletionLog(Base):
    __tablename__ = "deletion_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    sender_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    sender_is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    detected_domains: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    detected_telegram_entities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    message_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="deletion_logs")
