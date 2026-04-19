"""Create messages and notification attempt audit tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202604180003"
down_revision = "202604180002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create message submission and notification attempt audit tables."""

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("category_code", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("btrim(body) <> ''", name="ck_messages_body_not_blank"),
        sa.ForeignKeyConstraint(["category_code"], ["notification_categories.code"]),
    )
    op.create_index("ix_messages_category_code", "messages", ["category_code"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    op.create_table(
        "notification_attempts",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("channel_code", sa.String(length=32), nullable=False),
        sa.Column("category_code", sa.String(length=32), nullable=False),
        sa.Column("message_body", sa.Text(), nullable=False),
        sa.Column(
            "recipient_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "attempt_number",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column(
            "attempted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("delivered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempt_number > 0",
            name="ck_notification_attempts_attempt_number_positive",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed')",
            name="ck_notification_attempts_status",
        ),
        sa.CheckConstraint(
            "btrim(message_body) <> ''",
            name="ck_notification_attempts_message_body_not_blank",
        ),
        sa.ForeignKeyConstraint(["category_code"], ["notification_categories.code"]),
        sa.ForeignKeyConstraint(["channel_code"], ["notification_channels.code"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint(
            "message_id",
            "user_id",
            "channel_code",
            "attempt_number",
            name="uq_notification_attempts_attempt",
        ),
    )
    op.create_index(
        "ix_notification_attempts_attempted_at",
        "notification_attempts",
        ["attempted_at"],
    )
    op.create_index(
        "ix_notification_attempts_status",
        "notification_attempts",
        ["status"],
    )
    op.create_index(
        "ix_notification_attempts_user_id",
        "notification_attempts",
        ["user_id"],
    )
    op.create_index(
        "ix_notification_attempts_message_id",
        "notification_attempts",
        ["message_id"],
    )


def downgrade() -> None:
    """Drop message submission and notification attempt audit tables."""

    op.drop_index(
        "ix_notification_attempts_message_id",
        table_name="notification_attempts",
    )
    op.drop_index(
        "ix_notification_attempts_user_id",
        table_name="notification_attempts",
    )
    op.drop_index(
        "ix_notification_attempts_status",
        table_name="notification_attempts",
    )
    op.drop_index(
        "ix_notification_attempts_attempted_at",
        table_name="notification_attempts",
    )
    op.drop_table("notification_attempts")

    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_category_code", table_name="messages")
    op.drop_table("messages")
