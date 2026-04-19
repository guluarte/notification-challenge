"""Shared domain enumerations and canonical catalog definitions."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class MessageCategoryCatalogEntry:
    """Canonical category definition with a stable machine code and UI label."""

    code: MessageCategoryCode
    label: MessageCategory


@dataclass(frozen=True, slots=True)
class NotificationChannelCatalogEntry:
    """Canonical channel definition with a stable machine code and UI label."""

    code: NotificationChannelCode
    label: NotificationChannelType


MESSAGE_CATEGORY_CATALOG: tuple[MessageCategoryCatalogEntry, ...] = (
    MessageCategoryCatalogEntry(
        code=MessageCategoryCode.SPORTS,
        label=MessageCategory.SPORTS,
    ),
    MessageCategoryCatalogEntry(
        code=MessageCategoryCode.FINANCE,
        label=MessageCategory.FINANCE,
    ),
    MessageCategoryCatalogEntry(
        code=MessageCategoryCode.MOVIES,
        label=MessageCategory.MOVIES,
    ),
)

NOTIFICATION_CHANNEL_CATALOG: tuple[NotificationChannelCatalogEntry, ...] = (
    NotificationChannelCatalogEntry(
        code=NotificationChannelCode.SMS,
        label=NotificationChannelType.SMS,
    ),
    NotificationChannelCatalogEntry(
        code=NotificationChannelCode.EMAIL,
        label=NotificationChannelType.EMAIL,
    ),
    NotificationChannelCatalogEntry(
        code=NotificationChannelCode.PUSH,
        label=NotificationChannelType.PUSH,
    ),
)

MESSAGE_CATEGORY_CODES: tuple[MessageCategoryCode, ...] = tuple(
    entry.code for entry in MESSAGE_CATEGORY_CATALOG
)
NOTIFICATION_CHANNEL_CODES: tuple[NotificationChannelCode, ...] = tuple(
    entry.code for entry in NOTIFICATION_CHANNEL_CATALOG
)

MESSAGE_CATEGORY_LABELS_BY_CODE: dict[MessageCategoryCode, MessageCategory] = {
    entry.code: entry.label for entry in MESSAGE_CATEGORY_CATALOG
}
NOTIFICATION_CHANNEL_LABELS_BY_CODE: dict[
    NotificationChannelCode, NotificationChannelType
] = {entry.code: entry.label for entry in NOTIFICATION_CHANNEL_CATALOG}

CATEGORY_SEED_ROWS: tuple[tuple[str, str], ...] = (
    *((entry.code.value, entry.label.value) for entry in MESSAGE_CATEGORY_CATALOG),
)

CHANNEL_SEED_ROWS: tuple[tuple[str, str], ...] = (
    *((entry.code.value, entry.label.value) for entry in NOTIFICATION_CHANNEL_CATALOG),
)

DELIVERY_STATUS_VALUES: tuple[str, ...] = tuple(
    status.value for status in DeliveryStatus
)

__all__ = [
    "CATEGORY_SEED_ROWS",
    "CHANNEL_SEED_ROWS",
    "DELIVERY_STATUS_VALUES",
    "DeliveryStatus",
    "MESSAGE_CATEGORY_CATALOG",
    "MESSAGE_CATEGORY_CODES",
    "MESSAGE_CATEGORY_LABELS_BY_CODE",
    "MessageCategory",
    "MessageCategoryCatalogEntry",
    "MessageCategoryCode",
    "NOTIFICATION_CHANNEL_CATALOG",
    "NOTIFICATION_CHANNEL_CODES",
    "NOTIFICATION_CHANNEL_LABELS_BY_CODE",
    "NotificationChannelCatalogEntry",
    "NotificationChannelCode",
    "NotificationChannelType",
]
