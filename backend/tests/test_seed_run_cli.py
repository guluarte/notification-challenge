"""Tests for the database seed CLI entry point."""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch

from app.seeders.demo import SeedSummary
from app.seeders.run import main


class FakeSeedSession:
    """Minimal context-managed session double for seed CLI tests."""

    def __init__(self) -> None:
        self.commit_called = False

    def __enter__(self) -> "FakeSeedSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        del exc_type, exc, traceback

    def commit(self) -> None:
        self.commit_called = True


class FakeSessionFactory:
    """Return the same fake session whenever the CLI asks for one."""

    def __init__(self, session: FakeSeedSession) -> None:
        self.session = session

    def __call__(self) -> FakeSeedSession:
        return self.session


def test_seed_run_main_returns_zero_after_successful_seed() -> None:
    """The CLI should commit seeded data and exit successfully."""

    session = FakeSeedSession()
    summary = SeedSummary(
        categories=3,
        channels=3,
        users=4,
        category_subscriptions=8,
        channel_preferences=7,
    )

    with (
        patch("app.seeders.run.configure_logging") as configure_logging_mock,
        patch(
            "app.seeders.run.seed_database",
            return_value=summary,
        ) as seed_database_mock,
        patch(
            "app.seeders.run.SessionFactory",
            new=FakeSessionFactory(session),
        ),
        patch("app.seeders.run.engine.dispose") as dispose_mock,
    ):
        exit_code = main()

    assert exit_code == 0
    assert session.commit_called is True
    configure_logging_mock.assert_called_once()
    seed_database_mock.assert_called_once_with(session)
    dispose_mock.assert_called_once_with()


def test_seed_run_main_returns_one_for_sqlalchemy_failures() -> None:
    """SQLAlchemy failures should produce a non-zero exit code."""

    session = FakeSeedSession()

    with (
        patch("app.seeders.run.configure_logging"),
        patch(
            "app.seeders.run.seed_database",
            side_effect=SQLAlchemyError("seed failed"),
        ),
        patch(
            "app.seeders.run.SessionFactory",
            new=FakeSessionFactory(session),
        ),
        patch("app.seeders.run.engine.dispose") as dispose_mock,
    ):
        exit_code = main()

    assert exit_code == 1
    assert session.commit_called is False
    dispose_mock.assert_called_once_with()


def test_seed_run_main_returns_one_for_unexpected_failures() -> None:
    """Unexpected seed failures should also produce a non-zero exit code."""

    session = FakeSeedSession()

    with (
        patch("app.seeders.run.configure_logging"),
        patch("app.seeders.run.seed_database", side_effect=RuntimeError("boom")),
        patch(
            "app.seeders.run.SessionFactory",
            new=FakeSessionFactory(session),
        ),
        patch("app.seeders.run.engine.dispose") as dispose_mock,
    ):
        exit_code = main()

    assert exit_code == 1
    assert session.commit_called is False
    dispose_mock.assert_called_once_with()
