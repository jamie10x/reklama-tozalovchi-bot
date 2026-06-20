"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_chat_id", sa.BigInteger(), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("mode", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("bot_can_delete_messages", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("mode IN ('relaxed', 'normal', 'strict')", name="ck_chat_mode"),
    )

    op.create_table(
        "allowed_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_value", sa.String(255), nullable=False),
        sa.Column("telegram_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("entity_type IN ('user', 'bot', 'telegram_chat', 'domain')", name="ck_allowed_entity_type"),
        sa.UniqueConstraint("chat_id", "entity_type", "entity_value", name="uq_allowed_entity"),
    )

    op.create_index("ix_allowed_entities_chat_type", "allowed_entities", ["chat_id", "entity_type"])

    op.create_table(
        "deletion_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_user_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_is_bot", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("reasons", postgresql.JSONB(), nullable=True),
        sa.Column("detected_domains", postgresql.JSONB(), nullable=True),
        sa.Column("detected_telegram_entities", postgresql.JSONB(), nullable=True),
        sa.Column("message_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_deletion_logs_created_at", "deletion_logs", ["chat_id", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("deletion_logs")
    op.drop_table("allowed_entities")
    op.drop_table("chats")
