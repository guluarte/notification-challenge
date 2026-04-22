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

        statement = select(NotificationChannel).order_by(NotificationChannel.code.asc())
        channels = self.session.scalars(statement).all()
        return [
            NotificationCatalogItem(code=channel.code, label=channel.name)
            for channel in channels
        ]
