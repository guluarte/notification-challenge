"""Tests for notification dispatch orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.notification_dispatcher import NotificationDispatcherService
from app.services.types import DeliveryResult, PersistedMessage, ResolvedSubscriber


@dataclass
class RecordedAttempt:
    """Captured delivery repository updates for test assertions."""

    attempt_id: int
    channel_code: str
    status: str
    failure_reason: str | None = None
    provider_reference: str | None = None


class FakeDeliveryRepository:
    """Delivery repository double that records pending and final states."""

    def __init__(self) -> None:
        self.attempts: list[RecordedAttempt] = []
        self._next_id = 1

    def create_pending_attempt(
        self,
        *,
        message: PersistedMessage,
        subscriber: ResolvedSubscriber,
        channel_code: str,
    ) -> int:
        attempt_id = self._next_id
        self._next_id += 1
        self.attempts.append(
            RecordedAttempt(
                attempt_id=attempt_id,
                channel_code=channel_code,
                status="pending",
            )
        )
        return attempt_id

    def mark_sent(
        self,
        *,
        attempt_id: int,
        provider_reference: str | None,
        delivered_at: datetime,
    ) -> None:
        del delivered_at
        attempt = self._find(attempt_id)
        attempt.status = "sent"
        attempt.provider_reference = provider_reference
        attempt.failure_reason = None

    def mark_failed(self, *, attempt_id: int, failure_reason: str) -> None:
        attempt = self._find(attempt_id)
        attempt.status = "failed"
        attempt.failure_reason = failure_reason
        attempt.provider_reference = None

    def _find(self, attempt_id: int) -> RecordedAttempt:
        for attempt in self.attempts:
            if attempt.attempt_id == attempt_id:
                return attempt
        raise AssertionError(f"Unknown attempt id {attempt_id}")


class FakeStrategy:
    """Notification strategy double with optional failure behavior."""

    def __init__(self, *, provider_reference: str, should_fail: bool = False) -> None:
        self.provider_reference = provider_reference
        self.should_fail = should_fail
        self.calls: list[tuple[int, int]] = []

    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        self.calls.append((subscriber.user_id, message.id))
        if self.should_fail:
            raise RuntimeError("provider outage")
        return DeliveryResult(
            provider_reference=self.provider_reference,
            delivered_at=datetime.now(tz=timezone.utc),
        )


class FakeStrategyFactory:
    """Strategy registry double keyed by channel code."""

    def __init__(self, strategies: dict[str, FakeStrategy]) -> None:
        self.strategies = strategies

    def get_strategy(self, channel_code: str) -> FakeStrategy:
        strategy = self.strategies.get(channel_code)
        if strategy is None:
            raise RuntimeError(f"missing strategy for {channel_code}")
        return strategy


def test_notification_dispatcher_isolates_channel_failures() -> None:
    """One failed channel should not stop the remaining delivery attempts."""

    repository = FakeDeliveryRepository()
    factory = FakeStrategyFactory(
        strategies={
            "email": FakeStrategy(provider_reference="email-1"),
            "sms": FakeStrategy(provider_reference="sms-1", should_fail=True),
        }
    )
    service = NotificationDispatcherService(
        attempt_repository=repository,
        strategy_factory=factory,
    )
    message = PersistedMessage(
        id=10,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
    )
    subscribers = [
        ResolvedSubscriber(
            user_id=1,
            name="Alex",
            email="alex@example.com",
            phone_number="+15550000001",
            channel_codes=("email", "sms"),
        )
    ]

    summary = service.dispatch(message=message, subscribers=subscribers)

    assert summary.total_attempts == 2
    assert summary.sent == 1
    assert summary.failed == 1
    assert repository.attempts == [
        RecordedAttempt(
            attempt_id=1,
            channel_code="email",
            status="sent",
            provider_reference="email-1",
        ),
        RecordedAttempt(
            attempt_id=2,
            channel_code="sms",
            status="failed",
            failure_reason="provider outage",
        ),
    ]


def test_notification_dispatcher_handles_missing_strategy_as_attempt_failure() -> None:
    """An unconfigured strategy should fail only the affected attempt."""

    repository = FakeDeliveryRepository()
    service = NotificationDispatcherService(
        attempt_repository=repository,
        strategy_factory=FakeStrategyFactory(strategies={}),
    )
    message = PersistedMessage(
        id=11,
        category_code="movies",
        body="New release",
        created_at=datetime.now(tz=timezone.utc),
    )
    subscribers = [
        ResolvedSubscriber(
            user_id=4,
            name="Jordan",
            email="jordan@example.com",
            phone_number="+15550000002",
            channel_codes=("push",),
        )
    ]

    summary = service.dispatch(message=message, subscribers=subscribers)

    assert summary.total_attempts == 1
    assert summary.sent == 0
    assert summary.failed == 1
    assert repository.attempts == [
        RecordedAttempt(
            attempt_id=1,
            channel_code="push",
            status="failed",
            failure_reason="missing strategy for push",
        )
    ]
