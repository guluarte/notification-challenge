"""Read notification attempt history."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import InfrastructureError

from .types import NotificationLogEntry, NotificationLogRepositoryProtocol

logger = logging.getLogger(__name__)


class NotificationLogService:
    """Service for listing notification attempt history."""

    def __init__(self, attempt_repository: NotificationLogRepositoryProtocol) -> None:
        self.attempt_repository = attempt_repository

    def list_logs(self) -> list[NotificationLogEntry]:
        """Return notification attempt logs ordered newest first."""

        try:
            logs = self.attempt_repository.list_recent()
        except SQLAlchemyError as exc:
            logger.exception("Failed to load notification attempt logs")
            raise InfrastructureError(
                "The notification logs could not be loaded."
            ) from exc

        logger.info("Loaded %s notification attempt log rows", len(logs))
        return logs
