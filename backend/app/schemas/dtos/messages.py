"""DTOs for inbound message submission."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.enums import MessageCategoryCode


class CreateMessageRequestDTO(BaseModel):
    """Request payload for submitting a new notification message."""

    category: MessageCategoryCode
    body: str

    @field_validator("body", mode="before")
    @classmethod
    def normalize_body(cls, value: object) -> object:
        """Trim the request body and reject blank-only values."""

        if isinstance(value, str):
            normalized = value.strip()
            if normalized == "":
                raise ValueError("Message body must not be blank.")
            return normalized
        return value


class CreateMessageResponseDTO(BaseModel):
    """Response payload for a successfully submitted message."""

    message_id: int
    category: MessageCategoryCode
    body: str
    total_users: int
    total_attempts: int
    sent: int
    failed: int
    created_at: datetime
