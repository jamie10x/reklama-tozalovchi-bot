"""create secadmin schema and all tables

Revision ID: 0003
Revises: 0001
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "secadmin"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.execute("CREATE SEQUENCE IF NOT EXISTS secadmin.seq_event_number START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS secadmin.seq_case_number START 1")

    op.create_table(
        "security_observation_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("update_id", sa.BigInteger(), nullable=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("text_hash", sa.String(64), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("entities", postgresql.JSONB(), nullable=True),
        sa.Column("detection_result", postgresql.JSONB(), nullable=True),
        sa.Column("urls", postgresql.JSONB(), nullable=True),
        sa.Column("telegram_entities", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("locked_by", sa.String(64), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'claimed', 'completed', 'failed', 'expired')", name="ck_outbox_status"),
        schema=SCHEMA,
    )
    op.create_index("ix_outbox_status_created", "security_observation_outbox", ["status", "created_at"], schema=SCHEMA)
    op.create_index("ix_outbox_chat_message", "security_observation_outbox", ["chat_id", "message_id"], schema=SCHEMA)
    op.create_index("ix_outbox_locked_by", "security_observation_outbox", ["locked_by"], schema=SCHEMA)

    op.create_table(
        "security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_number", sa.BigInteger(), unique=True, nullable=False, server_default=sa.text("nextval('secadmin.seq_event_number')")),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("message_excerpt", sa.Text(), nullable=True),
        sa.Column("detection_reasons", postgresql.JSONB(), nullable=True),
        sa.Column("detected_indicators", postgresql.JSONB(), nullable=True),
        sa.Column("ad_score", sa.Integer(), nullable=True),
        sa.Column("security_score", sa.Integer(), nullable=True),
        sa.Column("ai_score", sa.Integer(), nullable=True),
        sa.Column("ai_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("ai_model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("assigned_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('open', 'claimed', 'confirmed', 'false_positive', 'escalated', 'resolved')", name="ck_event_status"),
        schema=SCHEMA,
    )
    op.create_index("ix_events_chat_id", "security_events", ["chat_id"], schema=SCHEMA)
    op.create_index("ix_events_sender_id", "security_events", ["sender_id"], schema=SCHEMA)
    op.create_index("ix_events_status_created", "security_events", ["status", "created_at"], schema=SCHEMA)
    op.create_index("ix_events_event_type", "security_events", ["event_type"], schema=SCHEMA)
    op.create_index("ix_events_severity", "security_events", ["severity"], schema=SCHEMA)
    op.create_index("ix_events_expires_at", "security_events", ["expires_at"], schema=SCHEMA)

    op.create_table(
        "indicators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("indicator_type", sa.String(30), nullable=False),
        sa.Column("indicator_value", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="suspected"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("chat_ids", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("indicator_type IN ('domain', 'url', 'telegram_username', 'telegram_bot', 'telegram_chat', 'email', 'phone', 'wallet', 'ip', 'file_hash', 'message_hash')", name="ck_indicator_type"),
        sa.CheckConstraint("status IN ('suspected', 'confirmed', 'blocked', 'allowed', 'false_positive', 'expired')", name="ck_indicator_status"),
        sa.UniqueConstraint("indicator_type", "indicator_value", name="uq_indicator_type_value"),
        schema=SCHEMA,
    )

    op.create_table(
        "event_indicators",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.security_events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("indicator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.indicators.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )

    op.create_table(
        "observed_users",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("current_username", sa.String(255), nullable=True),
        sa.Column("current_first_name", sa.String(255), nullable=True),
        sa.Column("current_last_name", sa.String(255), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("language_code", sa.String(10), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("photo_id", sa.String(255), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("risk_signals", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )

    op.create_table(
        "user_chat_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("secadmin.observed_users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("membership_status", sa.String(20), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("link_message_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_message_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("security_event_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confirmed_event_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_security_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "chat_id", name="uq_user_chat_profile"),
        schema=SCHEMA,
    )

    op.create_table(
        "user_observed_names",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("secadmin.observed_users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.create_index("ix_user_observed_names_user_id", "user_observed_names", ["user_id"], schema=SCHEMA)

    op.create_table(
        "member_risk_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("secadmin.observed_users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("signal_value", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )
    op.create_index("ix_member_risk_signals_user_chat", "member_risk_signals", ["user_id", "chat_id"], schema=SCHEMA)

    op.create_table(
        "officers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="analyst"),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('super_admin', 'analyst', 'responder', 'auditor')", name="ck_officer_role"),
        schema=SCHEMA,
    )

    op.create_table(
        "officer_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.officers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        schema=SCHEMA,
    )

    op.create_table(
        "officer_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.officers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )
    op.create_index("ix_audit_log_officer", "officer_audit_logs", ["officer_id"], schema=SCHEMA)
    op.create_index("ix_audit_log_resource", "officer_audit_logs", ["resource_type", "resource_id"], schema=SCHEMA)
    op.create_index("ix_audit_log_created", "officer_audit_logs", ["created_at"], schema=SCHEMA)

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_number", sa.BigInteger(), unique=True, nullable=False, server_default=sa.text("nextval('secadmin.seq_case_number')")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("assigned_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('open', 'in_progress', 'resolved', 'closed')", name="ck_case_status"),
        schema=SCHEMA,
    )
    op.create_table(
        "case_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.security_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_by_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("case_id", "event_id", name="uq_case_event"),
        schema=SCHEMA,
    )

    op.create_table(
        "case_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("officer_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )

    op.create_table(
        "enforcement_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("target_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("target_message_id", sa.BigInteger(), nullable=True),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("target_indicator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_by_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("locked_by", sa.String(64), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("action_type IN ('delete_message', 'trust_sender', 'block_indicator', 'allow_indicator', 'refresh_member', 'refresh_group_permissions', 'restrict_member', 'mute_member', 'ban_member')", name="ck_enforcement_action_type"),
        sa.CheckConstraint("status IN ('pending', 'claimed', 'completed', 'failed', 'cancelled')", name="ck_enforcement_status"),
        schema=SCHEMA,
    )

    op.create_table(
        "telegram_query_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("query_type", sa.String(30), nullable=False),
        sa.Column("target_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("requested_by_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("locked_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("query_type IN ('get_chat_member', 'get_user_profile_photos', 'get_chat_administrators', 'get_chat_member_count', 'get_chat')", name="ck_query_type"),
        schema=SCHEMA,
    )

    op.create_table(
        "ai_model_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )

    op.create_table(
        "ai_analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("input_text_hash", sa.String(64), nullable=True),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )

    op.create_table(
        "ai_message_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.ai_analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_suspicious", sa.Boolean(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("reasons", postgresql.JSONB(), nullable=True),
        sa.Column("recommended_action", sa.String(20), nullable=True),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("campaign_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )

    op.create_table(
        "message_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("text_hash", sa.String(64), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )

    op.create_table(
        "ai_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.ai_message_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("officer_id", sa.BigInteger(), nullable=True),
        sa.Column("was_correct", sa.Boolean(), nullable=True),
        sa.Column("correct_category", sa.String(50), nullable=True),
        sa.Column("correct_score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )

    op.create_table(
        "system_health_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    tables = [
        "system_health_events",
        "ai_feedback",
        "message_embeddings",
        "ai_message_analyses",
        "ai_analysis_jobs",
        "ai_model_registry",
        "telegram_query_requests",
        "enforcement_actions",
        "case_notes",
        "case_events",
        "cases",
        "officer_audit_logs",
        "officer_sessions",
        "officers",
        "member_risk_signals",
        "user_observed_names",
        "user_chat_profiles",
        "observed_users",
        "event_indicators",
        "indicators",
        "security_events",
        "security_observation_outbox",
    ]
    for table in tables:
        op.drop_table(table, schema=SCHEMA)
    op.execute("DROP SEQUENCE IF EXISTS secadmin.seq_event_number")
    op.execute("DROP SEQUENCE IF EXISTS secadmin.seq_case_number")
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA}")
