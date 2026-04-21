"""Routes for notification attempt audit history."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import NotificationLogServiceDep
from app.models.enums import MessageCategoryCode, NotificationChannelCode
from app.schemas.dtos import (
    ErrorResponseDTO,
    NotificationLogListItemDTO,
    NotificationLogListResponseDTO,
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
def list_logs(log_service: NotificationLogServiceDep) -> NotificationLogListResponseDTO:
    """Return notification attempt logs ordered from newest to oldest."""

    items = [_to_log_list_item(entry) for entry in log_service.list_logs()]
    return NotificationLogListResponseDTO(items=items)
