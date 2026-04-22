"""Read notification attempt history."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import InfrastructureError

from .types import (
    NotificationLogFilters,
    NotificationLogPage,
    NotificationLogRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class NotificationLogService:
    """Service for listing notification attempt history."""

    def __init__(self, attempt_repository: NotificationLogRepositoryProtocol) -> None:
        self.attempt_repository = attempt_repository

    def list_logs(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        filters: NotificationLogFilters | None = None,
    ) -> NotificationLogPage:
        """Return notification attempt logs ordered newest first."""

        normalized_filters = filters or NotificationLogFilters()

        try:
            logs = self.attempt_repository.list_recent(
                limit=limit,
                offset=offset,
                filters=normalized_filters,
            )
            total = self.attempt_repository.count_all(filters=normalized_filters)
        except SQLAlchemyError as exc:
            logger.exception("Failed to load notification attempt logs")
            raise InfrastructureError(
                "The notification logs could not be loaded."
            ) from exc

        logger.info(
            "Loaded %s notification attempt log rows with limit=%s offset=%s total=%s category=%s channel=%s status=%s message_id=%s user_id=%s search_present=%s",
            len(logs),
            limit,
            offset,
            total,
            normalized_filters.category_code,
            normalized_filters.channel_code,
            normalized_filters.status,
            normalized_filters.message_id,
            normalized_filters.user_id,
            normalized_filters.search is not None,
        )
        return NotificationLogPage(items=logs, total=total, limit=limit, offset=offset)
