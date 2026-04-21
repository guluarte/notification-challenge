"""Routes for notification attempt audit history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import NotificationLogServiceDep
from app.models.enums import MessageCategoryCode, NotificationChannelCode
from app.schemas.dtos import (
    ErrorResponseDTO,
    NotificationLogListItemDTO,
    NotificationLogListResponseDTO,
    NotificationLogPageSize,
    NotificationLogUserDTO,
)
from app.services.types import NotificationLogEntry

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
) -> NotificationLogListResponseDTO:
    """Return notification attempt logs ordered from newest to oldest."""

    page = log_service.list_logs(limit=limit.value, offset=offset)
    items = [_to_log_list_item(entry) for entry in page.items]
    return NotificationLogListResponseDTO(
        items=items,
        total=page.total,
        limit=limit,
        offset=page.offset,
    )
