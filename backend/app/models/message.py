"""Submitted message model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .category import NotificationCategory
    from .notification_delivery import NotificationAttempt


class Message(Base):
    """Inbound message submitted for fan-out delivery."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("btrim(body) <> ''", name="ck_messages_body_not_blank"),
        Index("ix_messages_category_code", "category_code"),
        Index("ix_messages_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    category_code: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("notification_categories.code", ondelete="RESTRICT"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    category: Mapped["NotificationCategory"] = relationship(back_populates="messages")
    notification_attempts: Mapped[list["NotificationAttempt"]] = relationship(
        back_populates="message"
    )
