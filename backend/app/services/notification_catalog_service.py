"""Read service for supported notification catalog options."""

from __future__ import annotations

import logging

from app.models.enums import MESSAGE_CATEGORY_CODES, NOTIFICATION_CHANNEL_CODES

from .types import (
    CatalogOptionRepositoryProtocol,
    NotificationCatalog,
    NotificationCatalogItem,
)

logger = logging.getLogger(__name__)


class NotificationCatalogService:
    """Load supported message categories and notification channels."""

    def __init__(
        self,
        *,
        category_repository: CatalogOptionRepositoryProtocol,
        channel_repository: CatalogOptionRepositoryProtocol,
    ) -> None:
        self.category_repository = category_repository
        self.channel_repository = channel_repository

    def get_catalog(self) -> NotificationCatalog:
        """Return catalog options in the canonical UI order."""

        categories = self._ordered_items(
            items=self.category_repository.list_all(),
            ordered_codes=tuple(code.value for code in MESSAGE_CATEGORY_CODES),
        )
        channels = self._ordered_items(
            items=self.channel_repository.list_all(),
            ordered_codes=tuple(code.value for code in NOTIFICATION_CHANNEL_CODES),
        )
        logger.info(
            "Loaded notification catalog categories=%s channels=%s",
            len(categories),
            len(channels),
        )
        return NotificationCatalog(categories=categories, channels=channels)

    @staticmethod
    def _ordered_items(
        *,
        items: list[NotificationCatalogItem],
        ordered_codes: tuple[str, ...],
    ) -> list[NotificationCatalogItem]:
        """Return catalog rows sorted by canonical enum order."""

        items_by_code = {item.code: item for item in items}
        ordered_items: list[NotificationCatalogItem] = []
        for code in ordered_codes:
            item = items_by_code.get(code)
            if item is not None:
                ordered_items.append(item)
        return ordered_items
