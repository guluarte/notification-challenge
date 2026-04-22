"""DTOs for notification catalog options."""

from pydantic import BaseModel

from app.models.enums import MessageCategoryCode, NotificationChannelCode


class NotificationCategoryOptionDTO(BaseModel):
    """Supported message category returned by the catalog endpoint."""

    code: MessageCategoryCode
    label: str


class NotificationChannelOptionDTO(BaseModel):
    """Supported delivery channel returned by the catalog endpoint."""

    code: NotificationChannelCode
    label: str


class NotificationCatalogResponseDTO(BaseModel):
    """Supported categories and delivery channels."""

    categories: list[NotificationCategoryOptionDTO]
    channels: list[NotificationChannelOptionDTO]
