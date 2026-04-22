"""FastAPI dependency for composing the notification catalog service."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.repositories.categories import NotificationCategoryRepository
from app.repositories.channels import NotificationChannelRepository
from app.services.notification_catalog_service import NotificationCatalogService

from .db import DBSessionDep


def get_notification_catalog_service(
    db_session: DBSessionDep,
) -> NotificationCatalogService:
    """Compose the catalog read service for the current request."""

    return NotificationCatalogService(
        category_repository=NotificationCategoryRepository(db_session),
        channel_repository=NotificationChannelRepository(db_session),
    )


NotificationCatalogServiceDep = Annotated[
    NotificationCatalogService, Depends(get_notification_catalog_service)
]
