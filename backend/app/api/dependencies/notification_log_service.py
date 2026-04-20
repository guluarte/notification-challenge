"""FastAPI dependency for composing the notification log service."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.repositories.notification_deliveries import NotificationAttemptRepository
from app.services.notification_log_service import NotificationLogService

from .db import DBSessionDep


def get_notification_log_service(db_session: DBSessionDep) -> NotificationLogService:
    """Compose the log listing service for the current request."""

    return NotificationLogService(
        attempt_repository=NotificationAttemptRepository(db_session)
    )


NotificationLogServiceDep = Annotated[
    NotificationLogService, Depends(get_notification_log_service)
]
