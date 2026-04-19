"""Tests for notification log listing behavior."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.enums import DeliveryStatus
from app.services.notification_log_service import NotificationLogService
from app.services.types import NotificationLogEntry


class FakeNotificationDeliveryRepository:
    """Delivery repository double for log listing tests."""

    def __init__(self, entries: list[NotificationLogEntry]) -> None:
        self.entries = entries
        self.calls = 0

    def list_recent(self) -> list[NotificationLogEntry]:
        self.calls += 1
        return self.entries


def test_notification_log_service_returns_repository_results() -> None:
    """The log service should delegate log retrieval to the repository."""

    entries = [
        NotificationLogEntry(
            delivery_id=1,
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
            delivered_at=datetime.now(tz=timezone.utc),
            failure_reason=None,
            provider_reference="email-7-2",
        )
    ]
    repository = FakeNotificationDeliveryRepository(entries=entries)
    service = NotificationLogService(delivery_repository=repository)

    result = service.list_logs()

    assert result == entries
    assert repository.calls == 1
