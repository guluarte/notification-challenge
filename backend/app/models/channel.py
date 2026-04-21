"""Notification channel catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class NotificationChannel(Base):
    """Catalog row for a supported delivery channel."""

    __tablename__ = "notification_channels"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user_preferences: Mapped[list[Any]] = relationship(
        "UserChannelPreference", back_populates="channel"
    )
    notification_attempts: Mapped[list[Any]] = relationship(
        "NotificationAttempt", back_populates="channel"
    )
