"""FastAPI dependency exports."""

from .db import DBSessionDep, get_db_session
from .services import (
    MessageServiceDep,
    NotificationCatalogServiceDep,
    NotificationLogServiceDep,
    get_message_service,
    get_notification_catalog_service,
    get_notification_log_service,
)

__all__ = [
    "DBSessionDep",
    "MessageServiceDep",
    "NotificationCatalogServiceDep",
    "NotificationLogServiceDep",
    "get_db_session",
    "get_message_service",
    "get_notification_catalog_service",
    "get_notification_log_service",
]
