"""Routes for notification attempt audit history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import NotificationLogServiceDep
from app.models.enums import (
    DeliveryStatus,
    MessageCategoryCode,
    NotificationChannelCode,
)
from app.schemas.dtos import (
    ErrorResponseDTO,
    NotificationLogListItemDTO,
    NotificationLogListResponseDTO,
    NotificationLogPageSize,
    NotificationLogUserDTO,
)
from app.services.types import NotificationLogEntry, NotificationLogFilters

router = APIRouter(prefix="/logs", tags=["logs"])


def _to_log_list_item(entry: NotificationLogEntry) -> NotificationLogListItemDTO:
    """Translate a service-layer log entry into the API response DTO."""

    return NotificationLogListItemDTO(
        attempt_id=entry.attempt_id,
        message_id=entry.message_id,
        category=MessageCategoryCode(entry.category_code),
        body=entry.body,
        user=NotificationLogUserDTO(
            id=entry.user_id,
            name=entry.user_name,
            email=entry.user_email,
            phone_number=entry.user_phone_number,
        ),
        channel=NotificationChannelCode(entry.channel_code),
        status=entry.status,
        attempt_number=entry.attempt_number,
        attempted_at=entry.attempted_at,
        processing_started_at=entry.processing_started_at,
        processed_at=entry.processed_at,
        delivered_at=entry.delivered_at,
        last_error_at=entry.last_error_at,
        next_retry_at=entry.next_retry_at,
        failure_reason=entry.failure_reason,
        provider_reference=entry.provider_reference,
    )


def _normalize_search_term(search: str | None) -> str | None:
    """Return a trimmed search term or no filter for blank input."""

    if search is None:
        return None

    normalized = search.strip()
    if normalized == "":
        return None
    return normalized


@router.get(
    "",
    response_model=NotificationLogListResponseDTO,
    responses={500: {"model": ErrorResponseDTO}},
    summary="List notification attempt logs",
)
def list_logs(
    log_service: NotificationLogServiceDep,
    limit: Annotated[
        NotificationLogPageSize,
        Query(description="Maximum number of log rows to return."),
    ] = NotificationLogPageSize.TEN,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of newest log rows to skip."),
    ] = 0,
    category: Annotated[
        MessageCategoryCode | None,
        Query(description="Only return attempts for this message category."),
    ] = None,
    channel: Annotated[
        NotificationChannelCode | None,
        Query(description="Only return attempts sent through this channel."),
    ] = None,
    status: Annotated[
        DeliveryStatus | None,
        Query(description="Only return attempts with this delivery status."),
    ] = None,
    message_id: Annotated[
        int | None,
        Query(gt=0, description="Only return attempts for this message id."),
    ] = None,
    user_id: Annotated[
        int | None,
        Query(gt=0, description="Only return attempts for this recipient user id."),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            alias="q",
            max_length=200,
            description="Case-insensitive search across message, recipient, provider, and failure text.",
        ),
    ] = None,
) -> NotificationLogListResponseDTO:
    """Return notification attempt logs ordered from newest to oldest."""

    filters = NotificationLogFilters(
        category_code=category.value if category is not None else None,
        channel_code=channel.value if channel is not None else None,
        status=status,
        message_id=message_id,
        user_id=user_id,
        search=_normalize_search_term(search),
    )
    page = log_service.list_logs(
        limit=limit.value,
        offset=offset,
        filters=filters,
    )
    items = [_to_log_list_item(entry) for entry in page.items]
    return NotificationLogListResponseDTO(
        items=items,
        total=page.total,
        limit=limit,
        offset=page.offset,
    )
