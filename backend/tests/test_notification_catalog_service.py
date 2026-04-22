"""Tests for notification catalog service behavior."""

from __future__ import annotations

from app.services.notification_catalog_service import NotificationCatalogService
from app.services.types import NotificationCatalogItem


class FakeCatalogRepository:
    """Repository double for catalog option lists."""

    def __init__(self, items: list[NotificationCatalogItem]) -> None:
        self.items = items

    def list_all(self) -> list[NotificationCatalogItem]:
        """Return configured catalog rows."""

        return self.items

    def exists(self, category_code: str) -> bool:
        """Return whether a configured row has the requested code."""

        return any(item.code == category_code for item in self.items)


def test_catalog_service_returns_options_in_canonical_order() -> None:
    """Catalog rows should use API enum order instead of database sort order."""

    service = NotificationCatalogService(
        category_repository=FakeCatalogRepository(
            [
                NotificationCatalogItem(code="movies", label="Movies"),
                NotificationCatalogItem(code="sports", label="Sports"),
                NotificationCatalogItem(code="finance", label="Finance"),
            ]
        ),
        channel_repository=FakeCatalogRepository(
            [
                NotificationCatalogItem(code="push", label="Push Notification"),
                NotificationCatalogItem(code="sms", label="SMS"),
                NotificationCatalogItem(code="email", label="E-Mail"),
            ]
        ),
    )

    catalog = service.get_catalog()

    assert catalog.categories == [
        NotificationCatalogItem(code="sports", label="Sports"),
        NotificationCatalogItem(code="finance", label="Finance"),
        NotificationCatalogItem(code="movies", label="Movies"),
    ]
    assert catalog.channels == [
        NotificationCatalogItem(code="sms", label="SMS"),
        NotificationCatalogItem(code="email", label="E-Mail"),
        NotificationCatalogItem(code="push", label="Push Notification"),
    ]
