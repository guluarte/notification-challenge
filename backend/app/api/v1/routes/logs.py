"""Routes for notification attempt audit history."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import NotificationLogServiceDep
from app.models.enums import MessageCategoryCode, NotificationChannelCode
from app.schemas.dtos import (
    ErrorResponseDTO,
    NotificationLogListItemDTO,
    NotificationLogListResponseDTO,
    NotificationRecipientDTO,
)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get(
    "",
    response_model=NotificationLogListResponseDTO,
    responses={500: {"model": ErrorResponseDTO}},
    summary="List notification attempt logs",
)
def list_logs(log_service: NotificationLogServiceDep) -> NotificationLogListResponseDTO:
    """Return notification attempt logs ordered from newest to oldest."""

    items = [
        NotificationLogListItemDTO(
            attempt_id=entry.attempt_id,
            message_id=entry.message_id,
            category=MessageCategoryCode(entry.category_code),
            body=entry.body,
            user=NotificationRecipientDTO(
                id=entry.user_id,
                name=entry.user_name,
                email=entry.user_email,
                phone_number=entry.user_phone_number,
            ),
            channel=NotificationChannelCode(entry.channel_code),
            status=entry.status,
            attempt_number=entry.attempt_number,
            attempted_at=entry.attempted_at,
            delivered_at=entry.delivered_at,
            failure_reason=entry.failure_reason,
            provider_reference=entry.provider_reference,
        )
        for entry in log_service.list_logs()
    ]
    return NotificationLogListResponseDTO(items=items)
