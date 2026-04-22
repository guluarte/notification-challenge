"""Add message idempotency keys."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202604210004"
down_revision = "202604190003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Store optional idempotency keys for duplicate submission protection."""

    op.add_column(
        "messages",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_check_constraint(
        "ck_messages_idempotency_key_not_blank",
        "messages",
        "idempotency_key IS NULL OR btrim(idempotency_key) <> ''",
    )
    op.create_index(
        "ix_messages_idempotency_key",
        "messages",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    """Remove message idempotency keys."""

    op.drop_index("ix_messages_idempotency_key", table_name="messages")
    op.drop_constraint(
        "ck_messages_idempotency_key_not_blank",
        "messages",
        type_="check",
    )
    op.drop_column("messages", "idempotency_key")
