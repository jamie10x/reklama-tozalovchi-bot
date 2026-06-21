import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.secadmin_base import SecAdminBase

SECADMIN_SCHEMA = "secadmin"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SecurityObservationOutbox(SecAdminBase):
    __tablename__ = "security_observation_outbox"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    update_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    text_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    detection_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    urls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    telegram_entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    locked_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'claimed', 'completed', 'failed', 'expired')",
            name="ck_outbox_status",
        ),
        Index("ix_outbox_status_created", "status", "created_at"),
        Index("ix_outbox_chat_message", "chat_id", "message_id"),
        Index("ix_outbox_locked_by", "locked_by"),
        {"schema": SECADMIN_SCHEMA},
    )


class GroupCaptureSetting(SecAdminBase):
    __tablename__ = "group_capture_settings"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capture_mode: Mapped[str] = mapped_column(String(20), default="flagged_only", nullable=False)
    metadata_retention_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    flagged_retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    updated_by_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "capture_mode IN ('metadata_only', 'flagged_only', 'full_text')",
            name="ck_capture_mode",
        ),
        {"schema": SECADMIN_SCHEMA},
    )


class SecurityEvent(SecAdminBase):
    __tablename__ = "security_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_number: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        server_default=text("nextval('secadmin.seq_event_number')"),
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    sender_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detection_reasons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    detected_indicators: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ad_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    security_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ai_model_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'claimed', 'confirmed', 'false_positive', 'escalated', 'resolved')",
            name="ck_event_status",
        ),
        Index("ix_events_chat_id", "chat_id"),
        Index("ix_events_sender_id", "sender_id"),
        Index("ix_events_status_created", "status", "created_at"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_severity", "severity"),
        Index("ix_events_expires_at", "expires_at"),
        {"schema": SECADMIN_SCHEMA},
    )

    indicators: Mapped[list["EventIndicator"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class ObservedMessage(SecAdminBase):
    __tablename__ = "observed_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    sender_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sender_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    message_type: Mapped[str] = mapped_column(String(30), default="text", nullable=False)
    text_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_stored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_text: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_forwarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    forward_from_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reply_to_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    detection_status: Mapped[str] = mapped_column(String(20), default="clean", nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ad_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    security_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detection_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("secadmin.security_events.id", ondelete="SET NULL"), nullable=True
    )
    message_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "detection_status IN ('clean', 'advertisement', 'security_threat', 'ai_review')",
            name="ck_observed_message_detection_status",
        ),
        UniqueConstraint("chat_id", "message_id", name="uq_observed_message_chat_message"),
        Index("ix_observed_messages_chat_created", "chat_id", "created_at"),
        Index("ix_observed_messages_sender", "sender_id"),
        Index("ix_observed_messages_status_created", "detection_status", "created_at"),
        Index("ix_observed_messages_event", "event_id"),
        {"schema": SECADMIN_SCHEMA},
    )


class EventIndicator(SecAdminBase):
    __tablename__ = "event_indicators"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secadmin.security_events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secadmin.indicators.id", ondelete="CASCADE"),
        primary_key=True,
    )
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["SecurityEvent"] = relationship(back_populates="indicators")
    indicator: Mapped["Indicator"] = relationship(back_populates="events")


class Indicator(SecAdminBase):
    __tablename__ = "indicators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_type: Mapped[str] = mapped_column(String(30), nullable=False)
    indicator_value: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="suspected", nullable=False)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    seen_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chat_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "indicator_type IN ('domain', 'url', 'telegram_username', 'telegram_bot', "
            "'telegram_chat', 'email', 'phone', 'wallet', 'ip', 'file_hash', 'message_hash')",
            name="ck_indicator_type",
        ),
        CheckConstraint(
            "status IN ('suspected', 'confirmed', 'blocked', 'allowed', 'false_positive', 'expired')",  # noqa: E501
            name="ck_indicator_status",
        ),
        UniqueConstraint("indicator_type", "indicator_value", name="uq_indicator_type_value"),
        {"schema": SECADMIN_SCHEMA},
    )

    events: Mapped[list["EventIndicator"]] = relationship(back_populates="indicator")


class ObservedUser(SecAdminBase):
    __tablename__ = "observed_users"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    current_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    photo_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_signals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    chat_profiles: Mapped[list["UserChatProfile"]] = relationship(back_populates="user")
    observed_names: Mapped[list["UserObservedName"]] = relationship(back_populates="user")
    risk_signals_list: Mapped[list["MemberRiskSignal"]] = relationship(
        back_populates="user", foreign_keys="MemberRiskSignal.user_id"
    )


class UserChatProfile(SecAdminBase):
    __tablename__ = "user_chat_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("secadmin.observed_users.telegram_id", ondelete="CASCADE"),
        nullable=False,
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    membership_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    link_message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    security_event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_security_event_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", name="uq_user_chat_profile"),
        {"schema": SECADMIN_SCHEMA},
    )

    user: Mapped["ObservedUser"] = relationship(back_populates="chat_profiles")


class UserObservedName(SecAdminBase):
    __tablename__ = "user_observed_names"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("secadmin.observed_users.telegram_id", ondelete="CASCADE"),
        nullable=False,
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_user_observed_names_user_id", "user_id"),
        {"schema": SECADMIN_SCHEMA},
    )

    user: Mapped["ObservedUser"] = relationship(back_populates="observed_names")


class MemberRiskSignal(SecAdminBase):
    __tablename__ = "member_risk_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("secadmin.observed_users.telegram_id", ondelete="CASCADE"),
        nullable=False,
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_member_risk_signals_user_chat", "user_id", "chat_id"),
        {"schema": SECADMIN_SCHEMA},
    )

    user: Mapped["ObservedUser"] = relationship(
        back_populates="risk_signals_list", foreign_keys=[user_id]
    )


class Officer(SecAdminBase):
    __tablename__ = "officers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="analyst", nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin', 'analyst', 'responder', 'auditor')",
            name="ck_officer_role",
        ),
        {"schema": SECADMIN_SCHEMA},
    )


class OfficerSession(SecAdminBase):
    __tablename__ = "officer_sessions"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("secadmin.officers.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class OfficerAuditLog(SecAdminBase):
    __tablename__ = "officer_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("secadmin.officers.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_audit_log_officer", "officer_id"),
        Index("ix_audit_log_resource", "resource_type", "resource_id"),
        Index("ix_audit_log_created", "created_at"),
        {"schema": SECADMIN_SCHEMA},
    )


class Case(SecAdminBase):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        server_default=text("nextval('secadmin.seq_case_number')"),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'closed')",
            name="ck_case_status",
        ),
        {"schema": SECADMIN_SCHEMA},
    )

    case_events: Mapped[list["CaseEvent"]] = relationship(back_populates="case")
    case_notes: Mapped[list["CaseNote"]] = relationship(back_populates="case")


class CaseEvent(SecAdminBase):
    __tablename__ = "case_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("secadmin.cases.id", ondelete="CASCADE"), nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secadmin.security_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    added_by_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    added_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("case_id", "event_id", name="uq_case_event"),
        {"schema": SECADMIN_SCHEMA},
    )

    case: Mapped["Case"] = relationship(back_populates="case_events")


class CaseNote(SecAdminBase):
    __tablename__ = "case_notes"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("secadmin.cases.id", ondelete="CASCADE"), nullable=False
    )
    officer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    case: Mapped["Case"] = relationship(back_populates="case_notes")


class EnforcementAction(SecAdminBase):
    __tablename__ = "enforcement_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_indicator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    requested_by_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    locked_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('delete_message', 'trust_sender', 'block_indicator', "
            "'allow_indicator', 'refresh_member', 'refresh_group_permissions', "
            "'restrict_member', 'mute_member', 'ban_member', 'get_chat_info', "
            "'get_chat_administrators', 'get_chat_member_count', "
            "'get_user_profile_photos', 'save_observed_state')",
            name="ck_enforcement_action_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'claimed', 'completed', 'failed', 'cancelled')",
            name="ck_enforcement_status",
        ),
        {"schema": SECADMIN_SCHEMA},
    )


class TelegramQueryRequest(SecAdminBase):
    __tablename__ = "telegram_query_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    requested_by_officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    locked_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "query_type IN ('get_chat_member', 'get_user_profile_photos', "
            "'get_chat_administrators', 'get_chat_member_count', 'get_chat')",
            name="ck_query_type",
        ),
        {"schema": SECADMIN_SCHEMA},
    )


class AiModelRegistry(SecAdminBase):
    __tablename__ = "ai_model_registry"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class AiAnalysisJob(SecAdminBase):
    __tablename__ = "ai_analysis_jobs"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    input_text_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AiMessageAnalysis(SecAdminBase):
    __tablename__ = "ai_message_analyses"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secadmin.ai_analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_suspicious: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    campaign_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class MessageEmbedding(SecAdminBase):
    __tablename__ = "message_embeddings"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    text_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class AiFeedback(SecAdminBase):
    __tablename__ = "ai_feedback"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secadmin.ai_message_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    officer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    was_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    correct_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    correct_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class SystemHealthEvent(SecAdminBase):
    __tablename__ = "system_health_events"
    __table_args__ = {"schema": SECADMIN_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
