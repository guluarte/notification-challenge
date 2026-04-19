"""Association model for user channel preferences."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .channel import NotificationChannel
from .user import User


class UserChannelPreference(Base):
    """Join row mapping a user to a preferred notification channel."""

    __tablename__ = "user_channel_preferences"
    __table_args__ = (
        Index(
            "ix_user_channel_preferences_channel_code",
            "channel_code",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    channel_code: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("notification_channels.code", ondelete="RESTRICT"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[User] = relationship(back_populates="channel_preferences")
    channel: Mapped[NotificationChannel] = relationship(
        back_populates="user_preferences"
    )
