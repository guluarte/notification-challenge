"""Repository access for notification channel catalogs."""

from __future__ import annotations

from sqlalchemy import select

from app.models import NotificationChannel
from app.services.types import NotificationCatalogItem

from .base import BaseRepository


class NotificationChannelRepository(BaseRepository):
    """Query helpers for the notification channel catalog."""

    def list_all(self) -> list[NotificationCatalogItem]:
        """Return all supported delivery channels."""

        statement = select(
            NotificationChannel.code,
            NotificationChannel.name,
        ).order_by(NotificationChannel.code.asc())
        return [
            NotificationCatalogItem(code=code, label=name)
            for code, name in self.session.execute(statement).tuples()
        ]
