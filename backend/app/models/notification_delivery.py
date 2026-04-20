"""Notification attempt audit model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .category import NotificationCategory
    from .channel import NotificationChannel
    from .message import Message
    from .user import User


class NotificationAttempt(Base):
    """Audit row for an attempted notification send."""

    __tablename__ = "notification_attempts"
    __table_args__ = (
        CheckConstraint(
            "attempt_number > 0",
            name="ck_notification_attempts_attempt_number_positive",
        ),
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed')",
            name="ck_notification_attempts_status",
        ),
        CheckConstraint(
            "btrim(message_body) <> ''",
            name="ck_notification_attempts_message_body_not_blank",
        ),
        UniqueConstraint(
            "message_id",
            "user_id",
            "channel_code",
            "attempt_number",
            name="uq_notification_attempts_attempt",
        ),
        Index("ix_notification_attempts_attempted_at", "attempted_at"),
        Index("ix_notification_attempts_next_retry_at", "next_retry_at"),
        Index("ix_notification_attempts_status", "status"),
        Index("ix_notification_attempts_user_id", "user_id"),
        Index("ix_notification_attempts_message_id", "message_id"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    channel_code: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("notification_channels.code", ondelete="RESTRICT"),
        nullable=False,
    )
    category_code: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("notification_categories.code", ondelete="RESTRICT"),
        nullable=False,
    )
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    message: Mapped["Message"] = relationship(back_populates="notification_attempts")
    user: Mapped["User"] = relationship(back_populates="notification_attempts")
    channel: Mapped["NotificationChannel"] = relationship(
        back_populates="notification_attempts"
    )
    category: Mapped["NotificationCategory"] = relationship(
        back_populates="notification_attempts"
    )
