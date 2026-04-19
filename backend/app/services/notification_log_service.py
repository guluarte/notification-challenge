"""Read notification delivery history."""

from __future__ import annotations

import logging

from .types import NotificationLogEntry, NotificationLogRepositoryProtocol

logger = logging.getLogger(__name__)


class NotificationLogService:
    """Service for listing notification delivery history."""

    def __init__(self, delivery_repository: NotificationLogRepositoryProtocol) -> None:
        self.delivery_repository = delivery_repository

    def list_logs(self) -> list[NotificationLogEntry]:
        """Return notification audit logs ordered newest first."""

        logs = self.delivery_repository.list_recent()
        logger.info("Loaded %s notification delivery log rows", len(logs))
        return logs
