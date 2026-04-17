"""Create seed_users table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202604180001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the bootstrap seed_users table."""

    op.create_table(
        "seed_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column(
            "categories", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("channels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("email", name="uq_seed_users_email"),
    )


def downgrade() -> None:
    """Drop the bootstrap seed_users table."""

    op.drop_table("seed_users")
