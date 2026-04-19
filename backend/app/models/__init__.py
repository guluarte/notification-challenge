"""SQLAlchemy ORM model registry."""

from .base import Base
from .category import NotificationCategory
from .channel import NotificationChannel
from .enums import (
    CATEGORY_SEED_ROWS,
    CHANNEL_SEED_ROWS,
    DELIVERY_STATUS_VALUES,
    DeliveryStatus,
    MESSAGE_CATEGORY_CATALOG,
    MESSAGE_CATEGORY_CODES,
    MESSAGE_CATEGORY_LABELS_BY_CODE,
    MessageCategory,
    MessageCategoryCode,
    NOTIFICATION_CHANNEL_CATALOG,
    NOTIFICATION_CHANNEL_CODES,
    NOTIFICATION_CHANNEL_LABELS_BY_CODE,
    NotificationChannelCode,
    NotificationChannelType,
)
from .message import Message
from .notification_delivery import NotificationAttempt
from .user import User
from .user_category_subscription import UserCategorySubscription
from .user_channel_preference import UserChannelPreference

__all__ = [
    "Base",
    "CATEGORY_SEED_ROWS",
    "CHANNEL_SEED_ROWS",
    "DELIVERY_STATUS_VALUES",
    "DeliveryStatus",
    "Message",
    "MESSAGE_CATEGORY_CATALOG",
    "MESSAGE_CATEGORY_CODES",
    "MESSAGE_CATEGORY_LABELS_BY_CODE",
    "MessageCategory",
    "MessageCategoryCode",
    "NotificationCategory",
    "NotificationChannel",
    "NOTIFICATION_CHANNEL_CATALOG",
    "NOTIFICATION_CHANNEL_CODES",
    "NOTIFICATION_CHANNEL_LABELS_BY_CODE",
    "NotificationChannelCode",
    "NotificationChannelType",
    "NotificationAttempt",
    "User",
    "UserCategorySubscription",
    "UserChannelPreference",
]
