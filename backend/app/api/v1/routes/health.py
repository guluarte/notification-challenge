"""Health-check routes used during project setup."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DBSessionDep
from app.core.db import database_is_healthy
from app.schemas.dtos import HealthResponseDTO, HealthState

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponseDTO, summary="Health check")
def read_health(db_session: DBSessionDep) -> HealthResponseDTO:
    """Return the current service and database status."""

    if not database_is_healthy(db_session):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        )

    return HealthResponseDTO(status=HealthState.OK, database=HealthState.OK)
