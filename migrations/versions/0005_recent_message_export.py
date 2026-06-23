"""allow recent message export command

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
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
        "'get_user_profile_photos', 'save_observed_state', 'send_recent_messages')",
        schema=SCHEMA,
    )


def downgrade() -> None:
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
