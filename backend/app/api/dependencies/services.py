"""Backward-compatible exports for service dependency composition."""

from __future__ import annotations

from .message_service import MessageServiceDep, get_message_service
from .notification_log_service import (
    NotificationLogServiceDep,
    get_notification_log_service,
)

__all__ = [
    "MessageServiceDep",
    "NotificationLogServiceDep",
    "get_message_service",
    "get_notification_log_service",
]
