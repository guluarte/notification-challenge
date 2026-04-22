"""Routes for inbound message submission."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.api.dependencies import MessageServiceDep
from app.models.enums import MessageCategoryCode
from app.schemas.dtos import (
    CreateMessageRequestDTO,
    CreateMessageResponseDTO,
    ErrorResponseDTO,
    ValidationErrorResponseDTO,
)

router = APIRouter(prefix="/messages", tags=["messages"])


def _normalize_idempotency_header(idempotency_key: str | None) -> str | None:
    """Normalize the optional idempotency header value."""

    if idempotency_key is None:
        return None

    normalized = idempotency_key.strip()
    if normalized == "":
        return None
    return normalized


@router.post(
    "",
    response_model=CreateMessageResponseDTO,
    responses={
        200: {"model": CreateMessageResponseDTO},
        409: {"model": ErrorResponseDTO},
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
    response: Response,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            max_length=128,
            description="Optional key used to replay duplicate submissions safely.",
        ),
    ] = None,
) -> CreateMessageResponseDTO:
    """Create a message and dispatch it to eligible subscribers."""

    normalized_idempotency_key = _normalize_idempotency_header(idempotency_key)
    result = message_service.create_message(
        category_code=payload.category.value,
        body=payload.body,
        idempotency_key=normalized_idempotency_key,
    )
    if result.was_duplicate:
        response.status_code = status.HTTP_200_OK

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
