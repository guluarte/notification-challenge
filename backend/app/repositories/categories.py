"""Repository access for notification category catalogs."""

from __future__ import annotations

from sqlalchemy import select

from app.models import NotificationCategory
from app.services.types import NotificationCatalogItem

from .base import BaseRepository


class NotificationCategoryRepository(BaseRepository):
    """Query helpers for the notification category catalog."""

    def exists(self, category_code: str) -> bool:
        """Return whether the category code exists in the catalog."""

        statement = select(NotificationCategory.code).where(
            NotificationCategory.code == category_code
        )
        return self.session.scalar(statement) is not None

    def list_all(self) -> list[NotificationCatalogItem]:
        """Return all supported message categories."""

        statement = select(NotificationCategory).order_by(
            NotificationCategory.code.asc()
        )
        categories = self.session.scalars(statement).all()
        return [
            NotificationCatalogItem(code=category.code, label=category.name)
            for category in categories
        ]
