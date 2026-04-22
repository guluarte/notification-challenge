"""Add notification log filter indexes."""

from __future__ import annotations

from alembic import op

revision = "202604220005"
down_revision = "202604210004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Index common audit-log filter columns."""

    op.create_index(
        "ix_notification_attempts_category_code",
        "notification_attempts",
        ["category_code"],
    )
    op.create_index(
        "ix_notification_attempts_channel_code",
        "notification_attempts",
        ["channel_code"],
    )


def downgrade() -> None:
    """Remove audit-log filter indexes."""

    op.drop_index(
        "ix_notification_attempts_channel_code",
        table_name="notification_attempts",
    )
    op.drop_index(
        "ix_notification_attempts_category_code",
        table_name="notification_attempts",
    )
