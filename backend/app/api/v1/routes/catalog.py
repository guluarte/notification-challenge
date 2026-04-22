"""Routes for supported notification catalog options."""

from fastapi import APIRouter

from app.api.dependencies import NotificationCatalogServiceDep
from app.models.enums import MessageCategoryCode, NotificationChannelCode
from app.schemas.dtos import (
    ErrorResponseDTO,
    NotificationCatalogResponseDTO,
    NotificationCategoryOptionDTO,
    NotificationChannelOptionDTO,
)
from app.services.types import NotificationCatalogItem

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _to_category_option(
    item: NotificationCatalogItem,
) -> NotificationCategoryOptionDTO:
    """Map a service catalog item into a category DTO."""

    return NotificationCategoryOptionDTO(
        code=MessageCategoryCode(item.code),
        label=item.label,
    )


def _to_channel_option(item: NotificationCatalogItem) -> NotificationChannelOptionDTO:
    """Map a service catalog item into a channel DTO."""

    return NotificationChannelOptionDTO(
        code=NotificationChannelCode(item.code),
        label=item.label,
    )


@router.get(
    "",
    response_model=NotificationCatalogResponseDTO,
    responses={500: {"model": ErrorResponseDTO}},
    summary="List supported notification catalog options",
)
def read_catalog(
    catalog_service: NotificationCatalogServiceDep,
) -> NotificationCatalogResponseDTO:
    """Return supported categories and delivery channels."""

    catalog = catalog_service.get_catalog()
    return NotificationCatalogResponseDTO(
        categories=[_to_category_option(item) for item in catalog.categories],
        channels=[_to_channel_option(item) for item in catalog.channels],
    )
