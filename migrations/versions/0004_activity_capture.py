"""add activity capture tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "secadmin"


def upgrade() -> None:
    op.drop_constraint("ck_enforcement_action_type", "enforcement_actions", schema=SCHEMA)
    op.create_check_constraint(
        "ck_enforcement_action_type",
        "enforcement_actions",
        "action_type IN ('delete_message', 'trust_sender', 'block_indicator', "
        "'allow_indicator', 'refresh_member', 'refresh_group_permissions', "
        "'restrict_member', 'mute_member', 'ban_member', 'get_chat_info', "
        "'get_chat_administrators', 'get_chat_member_count', "
        "'get_user_profile_photos', 'save_observed_state')",
        schema=SCHEMA,
    )

    op.create_table(
        "group_capture_settings",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capture_mode", sa.String(20), nullable=False, server_default="flagged_only"),
        sa.Column("metadata_retention_days", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("flagged_retention_days", sa.Integer(), nullable=False, server_default=sa.text("90")),
        sa.Column("updated_by_officer_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "capture_mode IN ('metadata_only', 'flagged_only', 'full_text')",
            name="ck_capture_mode",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "observed_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_username", sa.String(255), nullable=True),
        sa.Column("sender_first_name", sa.String(255), nullable=True),
        sa.Column("sender_last_name", sa.String(255), nullable=True),
        sa.Column("sender_is_bot", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sender_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("message_type", sa.String(30), nullable=False, server_default="text"),
        sa.Column("text_hash", sa.String(64), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("text_stored", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_text", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_edited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_forwarded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("forward_from_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("reply_to_message_id", sa.BigInteger(), nullable=True),
        sa.Column("entities", postgresql.JSONB(), nullable=True),
        sa.Column("detection_status", sa.String(20), nullable=False, server_default="clean"),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ad_score", sa.Integer(), nullable=True),
        sa.Column("security_score", sa.Integer(), nullable=True),
        sa.Column("ai_score", sa.Integer(), nullable=True),
        sa.Column("detection_result", postgresql.JSONB(), nullable=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("secadmin.security_events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "detection_status IN ('clean', 'advertisement', 'security_threat', 'ai_review')",
            name="ck_observed_message_detection_status",
        ),
        sa.UniqueConstraint("chat_id", "message_id", name="uq_observed_message_chat_message"),
        schema=SCHEMA,
    )
    op.create_index("ix_observed_messages_chat_created", "observed_messages", ["chat_id", "created_at"], schema=SCHEMA)
    op.create_index("ix_observed_messages_sender", "observed_messages", ["sender_id"], schema=SCHEMA)
    op.create_index("ix_observed_messages_status_created", "observed_messages", ["detection_status", "created_at"], schema=SCHEMA)
    op.create_index("ix_observed_messages_event", "observed_messages", ["event_id"], schema=SCHEMA)

    op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA secadmin TO secadmin_api")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'secadmin_reader') THEN
                GRANT SELECT ON ALL TABLES IN SCHEMA secadmin TO secadmin_reader;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_observed_messages_event", table_name="observed_messages", schema=SCHEMA)
    op.drop_index("ix_observed_messages_status_created", table_name="observed_messages", schema=SCHEMA)
    op.drop_index("ix_observed_messages_sender", table_name="observed_messages", schema=SCHEMA)
    op.drop_index("ix_observed_messages_chat_created", table_name="observed_messages", schema=SCHEMA)
    op.drop_table("observed_messages", schema=SCHEMA)
    op.drop_table("group_capture_settings", schema=SCHEMA)
    op.drop_constraint("ck_enforcement_action_type", "enforcement_actions", schema=SCHEMA)
    op.create_check_constraint(
        "ck_enforcement_action_type",
        "enforcement_actions",
        "action_type IN ('delete_message', 'trust_sender', 'block_indicator', "
        "'allow_indicator', 'refresh_member', 'refresh_group_permissions', "
        "'restrict_member', 'mute_member', 'ban_member')",
        schema=SCHEMA,
    )
