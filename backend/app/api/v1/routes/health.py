"""Health-check routes used during project setup."""

from fastapi import APIRouter

from app.api.dependencies import DBSessionDep
from app.core.exceptions import ServiceUnavailableError
from app.core.db import database_is_healthy
from app.schemas.dtos import ErrorResponseDTO, HealthResponseDTO, HealthState

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponseDTO,
    responses={503: {"model": ErrorResponseDTO}},
    summary="Health check",
)
def read_health(db_session: DBSessionDep) -> HealthResponseDTO:
    """Return the current service and database status."""

    if not database_is_healthy(db_session):
        raise ServiceUnavailableError("Database unavailable.")

    return HealthResponseDTO(status=HealthState.OK, database=HealthState.OK)
