"""Shared domain enumerations and seed constants."""

from __future__ import annotations

from enum import StrEnum


class MessageCategory(StrEnum):
    """Supported notification message categories."""

    SPORTS = "Sports"
    FINANCE = "Finance"
    MOVIES = "Movies"


class MessageCategoryCode(StrEnum):
    """Stable category codes used by the API and persistence layers."""

    SPORTS = "sports"
    FINANCE = "finance"
    MOVIES = "movies"


class NotificationChannelType(StrEnum):
    """Supported outbound notification channels."""

    SMS = "SMS"
    EMAIL = "E-Mail"
    PUSH = "Push Notification"


class NotificationChannelCode(StrEnum):
    """Stable notification channel codes used by persistence and routing."""

    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class DeliveryStatus(StrEnum):
    """Allowed notification delivery states."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


CATEGORY_SEED_ROWS: tuple[tuple[str, str], ...] = (
    (MessageCategoryCode.SPORTS.value, MessageCategory.SPORTS.value),
    (MessageCategoryCode.FINANCE.value, MessageCategory.FINANCE.value),
    (MessageCategoryCode.MOVIES.value, MessageCategory.MOVIES.value),
)

CHANNEL_SEED_ROWS: tuple[tuple[str, str], ...] = (
    (NotificationChannelCode.SMS.value, NotificationChannelType.SMS.value),
    (NotificationChannelCode.EMAIL.value, NotificationChannelType.EMAIL.value),
    (NotificationChannelCode.PUSH.value, NotificationChannelType.PUSH.value),
)

DELIVERY_STATUS_VALUES: tuple[str, ...] = tuple(
    status.value for status in DeliveryStatus
)
