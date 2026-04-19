"""Tests for database-backed health checks."""

from typing import cast
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.routes.health import read_health
from app.core.exceptions import ServiceUnavailableError
from app.core.db import database_is_healthy
from app.main import create_app
from app.schemas.dtos import HealthResponseDTO, HealthState


class FakeSession:
    """Minimal session double used to validate the health probe query."""

    def __init__(self, scalar_result: object) -> None:
        self.scalar_result = scalar_result
        self.last_statement: object | None = None

    def scalar(self, statement: object) -> object:
        self.last_statement = statement
        return self.scalar_result


class FailingSession:
    """Minimal session double that raises a SQLAlchemy error on query."""

    def scalar(self, _statement: object) -> object:
        raise SQLAlchemyError("database unavailable")


def test_database_is_healthy_runs_a_select_one_probe() -> None:
    """The DB probe should execute a trivial query through the shared session."""

    fake_session = FakeSession(scalar_result=1)

    assert database_is_healthy(cast(Session, fake_session)) is True

    assert fake_session.last_statement is not None


def test_database_is_healthy_returns_false_on_sqlalchemy_errors() -> None:
    """The DB probe should convert SQLAlchemy failures into an unhealthy result."""

    assert database_is_healthy(cast(Session, FailingSession())) is False


def test_read_health_returns_ok_when_database_check_succeeds() -> None:
    """The route should report healthy when the DB probe succeeds."""

    fake_session = cast(Session, object())

    with patch("app.api.v1.routes.health.database_is_healthy", return_value=True):
        response = read_health(fake_session)

    assert response == HealthResponseDTO(
        status=HealthState.OK,
        database=HealthState.OK,
    )
    assert response.model_dump(mode="json") == {"status": "ok", "database": "ok"}


def test_read_health_returns_503_when_database_check_fails() -> None:
    """The route should surface database outages as service unavailable."""

    fake_session = cast(Session, object())

    with patch("app.api.v1.routes.health.database_is_healthy", return_value=False):
        try:
            read_health(fake_session)
        except ServiceUnavailableError as exc:
            assert exc.status_code == 503
            assert exc.detail == "Database unavailable."
        else:
            raise AssertionError(
                "Expected the health route to raise ServiceUnavailableError"
            )


def test_health_route_is_served_under_the_versioned_api_prefix() -> None:
    """The health endpoint should be mounted under the configured API prefix."""

    app = create_app()

    assert app.url_path_for("read_health") == "/v1/health"
