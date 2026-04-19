"""DTOs for API error responses."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponseDTO(BaseModel):
    """Generic API error payload."""

    detail: str
    code: str


class ValidationErrorItemDTO(BaseModel):
    """Single validation issue returned by the API."""

    field: str
    message: str


class ValidationErrorResponseDTO(BaseModel):
    """Validation error payload returned by request handlers."""

    detail: str
    code: str
    errors: list[ValidationErrorItemDTO]
