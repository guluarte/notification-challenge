"""Read notification attempt history."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import InfrastructureError

from .types import NotificationLogPage, NotificationLogRepositoryProtocol

logger = logging.getLogger(__name__)


class NotificationLogService:
    """Service for listing notification attempt history."""

    def __init__(self, attempt_repository: NotificationLogRepositoryProtocol) -> None:
        self.attempt_repository = attempt_repository

    def list_logs(self, *, limit: int = 10, offset: int = 0) -> NotificationLogPage:
        """Return notification attempt logs ordered newest first."""

        try:
            logs = self.attempt_repository.list_recent(limit=limit, offset=offset)
            total = self.attempt_repository.count_all()
        except SQLAlchemyError as exc:
            logger.exception("Failed to load notification attempt logs")
            raise InfrastructureError(
                "The notification logs could not be loaded."
            ) from exc

        logger.info(
            "Loaded %s notification attempt log rows with limit=%s offset=%s total=%s",
            len(logs),
            limit,
            offset,
            total,
        )
        return NotificationLogPage(items=logs, total=total, limit=limit, offset=offset)
