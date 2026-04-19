"""Routes for inbound message submission."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.dependencies import MessageServiceDep
from app.models.enums import MessageCategoryCode
from app.schemas.dtos import (
    CreateMessageRequestDTO,
    CreateMessageResponseDTO,
    ErrorResponseDTO,
    ValidationErrorResponseDTO,
)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post(
    "",
    response_model=CreateMessageResponseDTO,
    responses={
        422: {"model": ValidationErrorResponseDTO},
        500: {"model": ErrorResponseDTO},
        503: {"model": ErrorResponseDTO},
    },
    status_code=status.HTTP_201_CREATED,
    summary="Submit a notification message",
)
def create_message(
    payload: CreateMessageRequestDTO,
    message_service: MessageServiceDep,
) -> CreateMessageResponseDTO:
    """Create a message and dispatch it to eligible subscribers."""

    result = message_service.create_message(
        category_code=payload.category.value,
        body=payload.body,
    )
    return CreateMessageResponseDTO(
        message_id=result.message_id,
        category=MessageCategoryCode(result.category_code),
        body=result.body,
        total_users=result.total_users,
        total_attempts=result.total_attempts,
        sent=result.sent,
        failed=result.failed,
        created_at=result.created_at,
    )
