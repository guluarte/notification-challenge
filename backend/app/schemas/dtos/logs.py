"""DTOs for notification attempt logs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import (
    DeliveryStatus,
    MessageCategoryCode,
    NotificationChannelCode,
)


class NotificationLogListItemDTO(BaseModel):
    """Single notification attempt row returned by the API."""

    attempt_id: int
    message_id: int
    category: MessageCategoryCode
    body: str
    channel: NotificationChannelCode
    status: DeliveryStatus
    attempt_number: int
    attempted_at: datetime
    processing_started_at: datetime | None
    processed_at: datetime | None
    delivered_at: datetime | None
    last_error_at: datetime | None
    next_retry_at: datetime | None
    failure_reason: str | None
    provider_reference: str | None


class NotificationLogListResponseDTO(BaseModel):
    """Collection of delivery log rows."""

    items: list[NotificationLogListItemDTO]
