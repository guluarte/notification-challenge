"""Tests for FastAPI database dependencies."""

from unittest.mock import patch

from app.api.dependencies import get_db_session
from app.core.exceptions import ServiceUnavailableError
from fastapi.exceptions import RequestValidationError


class FakeSession:
    """Minimal context-managed session double for dependency tests."""

    def __init__(self) -> None:
        self.rollback_called = False
        self.closed = False

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.closed = True

    def rollback(self) -> None:
        self.rollback_called = True


class FakeSessionFactory:
    """Return the same fake session each time the factory is invoked."""

    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def __call__(self) -> FakeSession:
        return self.session


def test_get_db_session_yields_request_scoped_session() -> None:
    """The dependency should yield the session and close it afterward."""

    fake_session = FakeSession()

    with patch(
        "app.api.dependencies.db.SessionFactory",
        new=FakeSessionFactory(fake_session),
    ):
        dependency = get_db_session()

        assert next(dependency) is fake_session

        try:
            next(dependency)
        except StopIteration:
            pass
        else:
            raise AssertionError("Expected dependency generator to stop")

    assert fake_session.rollback_called is False
    assert fake_session.closed is True


def test_get_db_session_rolls_back_when_handler_raises() -> None:
    """The dependency should roll back the session on request errors."""

    fake_session = FakeSession()

    with patch(
        "app.api.dependencies.db.SessionFactory",
        new=FakeSessionFactory(fake_session),
    ):
        dependency = get_db_session()
        next(dependency)

        try:
            dependency.throw(RuntimeError("boom"))
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected thrown exception to propagate")

    assert fake_session.rollback_called is True
    assert fake_session.closed is True


def test_get_db_session_rolls_back_handled_application_errors_without_error_log() -> (
    None
):
    """Handled application errors should not emit dependency error logs."""

    fake_session = FakeSession()

    with (
        patch(
            "app.api.dependencies.db.SessionFactory",
            new=FakeSessionFactory(fake_session),
        ),
        patch("app.api.dependencies.db.logger.exception") as logger_exception_mock,
    ):
        dependency = get_db_session()
        next(dependency)

        try:
            dependency.throw(ServiceUnavailableError("catalog unavailable"))
        except ServiceUnavailableError:
            pass
        else:
            raise AssertionError("Expected ServiceUnavailableError to propagate")

    assert fake_session.rollback_called is True
    assert fake_session.closed is True
    logger_exception_mock.assert_not_called()


def test_get_db_session_rolls_back_validation_errors_without_error_log() -> None:
    """Validation errors should roll back quietly and rely on the route handler."""

    fake_session = FakeSession()
    validation_error = RequestValidationError(
        [
            {
                "type": "value_error",
                "loc": ("body", "body"),
                "msg": "Value error, Message body must not be blank.",
                "input": "   ",
                "ctx": {"error": ValueError("Message body must not be blank.")},
            }
        ]
    )

    with (
        patch(
            "app.api.dependencies.db.SessionFactory",
            new=FakeSessionFactory(fake_session),
        ),
        patch("app.api.dependencies.db.logger.exception") as logger_exception_mock,
    ):
        dependency = get_db_session()
        next(dependency)

        try:
            dependency.throw(validation_error)
        except RequestValidationError:
            pass
        else:
            raise AssertionError("Expected RequestValidationError to propagate")

    assert fake_session.rollback_called is True
    assert fake_session.closed is True
    logger_exception_mock.assert_not_called()
