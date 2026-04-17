"""Shared domain enumerations and seed constants."""

from __future__ import annotations

from enum import StrEnum


class MessageCategory(StrEnum):
    """Supported notification message categories."""

    SPORTS = "Sports"
    FINANCE = "Finance"
    MOVIES = "Movies"


class NotificationChannelType(StrEnum):
    """Supported outbound notification channels."""

    SMS = "SMS"
    EMAIL = "E-Mail"
    PUSH = "Push Notification"


class DeliveryStatus(StrEnum):
    """Allowed notification delivery states."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


CATEGORY_SEED_ROWS: tuple[tuple[str, str], ...] = (
    ("sports", MessageCategory.SPORTS.value),
    ("finance", MessageCategory.FINANCE.value),
    ("movies", MessageCategory.MOVIES.value),
)

CHANNEL_SEED_ROWS: tuple[tuple[str, str], ...] = (
    ("sms", NotificationChannelType.SMS.value),
    ("email", NotificationChannelType.EMAIL.value),
    ("push", NotificationChannelType.PUSH.value),
)

DELIVERY_STATUS_VALUES: tuple[str, ...] = tuple(
    status.value for status in DeliveryStatus
)
