"""Association model for user category subscriptions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .category import NotificationCategory
from .user import User


class UserCategorySubscription(Base):
    """Join row mapping a user to a subscribed category."""

    __tablename__ = "user_category_subscriptions"
    __table_args__ = (
        Index(
            "ix_user_category_subscriptions_category_code",
            "category_code",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_code: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("notification_categories.code", ondelete="RESTRICT"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[User] = relationship(back_populates="category_subscriptions")
    category: Mapped[NotificationCategory] = relationship(
        back_populates="subscriptions"
    )
