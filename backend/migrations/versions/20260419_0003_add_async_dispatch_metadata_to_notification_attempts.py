"""Add async dispatch metadata to notification attempt audit rows."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202604190003"
down_revision = "202604180002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add processing and retry metadata for async-ready dispatching."""

    op.add_column(
        "notification_attempts",
        sa.Column("processing_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_attempts",
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_attempts",
        sa.Column("last_error_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_attempts",
        sa.Column("next_retry_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_notification_attempts_next_retry_at",
        "notification_attempts",
        ["next_retry_at"],
    )
    op.execute(
        """
        UPDATE notification_attempts
        SET
            processing_started_at = CASE
                WHEN status = 'pending' THEN NULL
                ELSE attempted_at
            END,
            processed_at = CASE
                WHEN status = 'pending' THEN NULL
                ELSE COALESCE(delivered_at, attempted_at)
            END,
            last_error_at = CASE
                WHEN status = 'failed' THEN attempted_at
                ELSE NULL
            END
        """
    )


def downgrade() -> None:
    """Drop async dispatch metadata from notification attempt audit rows."""

    op.drop_index(
        "ix_notification_attempts_next_retry_at",
        table_name="notification_attempts",
    )
    op.drop_column("notification_attempts", "next_retry_at")
    op.drop_column("notification_attempts", "last_error_at")
    op.drop_column("notification_attempts", "processed_at")
    op.drop_column("notification_attempts", "processing_started_at")
