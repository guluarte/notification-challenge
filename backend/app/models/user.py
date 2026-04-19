"""User model for seeded notification recipients."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .notification_delivery import NotificationAttempt
    from .user_category_subscription import UserCategorySubscription
    from .user_channel_preference import UserChannelPreference


class User(Base):
    """Notification recipient with channel and category preferences."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    category_subscriptions: Mapped[list["UserCategorySubscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    channel_preferences: Mapped[list["UserChannelPreference"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_attempts: Mapped[list["NotificationAttempt"]] = relationship(
        back_populates="user"
    )
