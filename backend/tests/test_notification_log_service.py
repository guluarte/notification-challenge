"""Tests for notification log listing behavior."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import InfrastructureError
from app.models.enums import DeliveryStatus
from app.services.notification_log_service import NotificationLogService
from app.services.types import NotificationLogEntry


class FakeNotificationAttemptRepository:
    """Attempt repository double for log listing tests."""

    def __init__(self, entries: list[NotificationLogEntry]) -> None:
        self.entries = entries
        self.list_calls: list[tuple[int, int]] = []
        self.count_calls = 0

    def list_recent(self, *, limit: int, offset: int) -> list[NotificationLogEntry]:
        self.list_calls.append((limit, offset))
        return self.entries

    def count_all(self) -> int:
        self.count_calls += 1
        return len(self.entries)


class FailingNotificationAttemptRepository:
    """Attempt repository double that simulates database failures."""

    def list_recent(self, *, limit: int, offset: int) -> list[NotificationLogEntry]:
        del limit, offset
        raise SQLAlchemyError("database unavailable")

    def count_all(self) -> int:
        raise AssertionError("count_all should not run after list_recent fails")


def test_notification_log_service_returns_repository_results() -> None:
    """The log service should delegate log retrieval to the repository."""

    entries = [
        NotificationLogEntry(
            attempt_id=1,
            message_id=7,
            category_code="sports",
            body="Final score",
            user_id=2,
            user_name="Jordan",
            user_email="jordan@example.com",
            user_phone_number="+15550000002",
            channel_code="email",
            status=DeliveryStatus.SENT,
            attempt_number=1,
            attempted_at=datetime.now(tz=timezone.utc),
            processing_started_at=datetime.now(tz=timezone.utc),
            processed_at=datetime.now(tz=timezone.utc),
            delivered_at=datetime.now(tz=timezone.utc),
            last_error_at=None,
            next_retry_at=None,
            failure_reason=None,
            provider_reference="email-7-2",
        )
    ]
    repository = FakeNotificationAttemptRepository(entries=entries)
    service = NotificationLogService(attempt_repository=repository)

    result = service.list_logs(limit=50, offset=100)

    assert result.items == entries
    assert result.total == 1
    assert result.limit == 50
    assert result.offset == 100
    assert repository.list_calls == [(50, 100)]
    assert repository.count_calls == 1


def test_notification_log_service_wraps_database_failures() -> None:
    """The log service should raise a structured error on repository failures."""

    service = NotificationLogService(
        attempt_repository=FailingNotificationAttemptRepository()
    )

    try:
        service.list_logs()
    except InfrastructureError as exc:
        assert str(exc) == "The notification logs could not be loaded."
    else:
        raise AssertionError("Expected InfrastructureError")
