"""DTOs for health-check responses."""

from enum import StrEnum

from pydantic import BaseModel


class HealthState(StrEnum):
    """Allowed health values exposed by the API schema."""

    OK = "ok"


class HealthResponseDTO(BaseModel):
    """Response payload for the health endpoint."""

    status: HealthState
    database: HealthState
