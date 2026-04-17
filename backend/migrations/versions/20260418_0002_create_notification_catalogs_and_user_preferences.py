"""Create catalogs, users, and preference tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202604180002"
down_revision = "202604180001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create normalized user and catalog tables."""

    op.create_table(
        "notification_categories",
        sa.Column("code", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("name", name="uq_notification_categories_name"),
    )

    op.create_table(
        "notification_channels",
        sa.Column("code", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("name", name="uq_notification_channels_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_created_at", "users", ["created_at"])

    op.create_table(
        "user_category_subscriptions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_code", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["category_code"], ["notification_categories.code"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "user_id",
            "category_code",
            name="pk_user_category_subscriptions",
        ),
    )
    op.create_index(
        "ix_user_category_subscriptions_category_code",
        "user_category_subscriptions",
        ["category_code"],
    )

    op.create_table(
        "user_channel_preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("channel_code", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["channel_code"], ["notification_channels.code"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "user_id",
            "channel_code",
            name="pk_user_channel_preferences",
        ),
    )
    op.create_index(
        "ix_user_channel_preferences_channel_code",
        "user_channel_preferences",
        ["channel_code"],
    )


def downgrade() -> None:
    """Drop normalized user and catalog tables."""

    op.drop_index(
        "ix_user_channel_preferences_channel_code",
        table_name="user_channel_preferences",
    )
    op.drop_table("user_channel_preferences")

    op.drop_index(
        "ix_user_category_subscriptions_category_code",
        table_name="user_category_subscriptions",
    )
    op.drop_table("user_category_subscriptions")

    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_table("users")

    op.drop_table("notification_channels")
    op.drop_table("notification_categories")
