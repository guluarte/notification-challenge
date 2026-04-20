"""Tests for notification dispatch orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.notification_dispatcher import NotificationDispatcherService
from app.services.types import (
    DeliveryResult,
    PendingNotificationAttempt,
    PersistedMessage,
    ResolvedSubscriber,
)


@dataclass
class RecordedAttempt:
    """Captured delivery repository updates for test assertions."""

    attempt_id: int
    message_id: int
    category_code: str
    message_body: str
    message_created_at: datetime
    user_id: int
    user_name: str
    user_email: str
    user_phone_number: str
    channel_code: str
    attempt_number: int
    status: str
    processing_started_at: datetime | None = None
    processed_at: datetime | None = None
    next_retry_at: datetime | None = None
    failure_reason: str | None = None
    provider_reference: str | None = None


class FakeDeliveryRepository:
    """Delivery repository double that records pending and final states."""

    def __init__(self) -> None:
        self.attempts: list[RecordedAttempt] = []
        self.delivered_timestamps: dict[int, datetime] = {}
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
                message_id=message.id,
                category_code=message.category_code,
                message_body=message.body,
                message_created_at=message.created_at,
                user_id=subscriber.user_id,
                user_name=subscriber.name,
                user_email=subscriber.email,
                user_phone_number=subscriber.phone_number,
                channel_code=channel_code,
                attempt_number=1,
                status="pending",
            )
        )
        return attempt_id

    def list_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> list[PendingNotificationAttempt]:
        pending_attempts = [
            attempt
            for attempt in self.attempts
            if attempt.status == "pending"
            and (message_id is None or attempt.message_id == message_id)
        ]
        if limit is not None:
            pending_attempts = pending_attempts[:limit]

        return [
            PendingNotificationAttempt(
                attempt_id=attempt.attempt_id,
                message=PersistedMessage(
                    id=attempt.message_id,
                    category_code=attempt.category_code,
                    body=attempt.message_body,
                    created_at=attempt.message_created_at,
                ),
                subscriber=ResolvedSubscriber(
                    user_id=attempt.user_id,
                    name=attempt.user_name,
                    email=attempt.user_email,
                    phone_number=attempt.user_phone_number,
                    channel_codes=(attempt.channel_code,),
                ),
                channel_code=attempt.channel_code,
                attempt_number=attempt.attempt_number,
            )
            for attempt in pending_attempts
        ]

    def mark_processing_started(
        self,
        *,
        attempt_id: int,
        processing_started_at: datetime,
    ) -> None:
        attempt = self._find(attempt_id)
        attempt.processing_started_at = processing_started_at

    def mark_sent(
        self,
        *,
        attempt_id: int,
        provider_reference: str | None,
        delivered_at: datetime,
    ) -> None:
        self.delivered_timestamps[attempt_id] = delivered_at
        attempt = self._find(attempt_id)
        attempt.status = "sent"
        attempt.processed_at = delivered_at
        attempt.next_retry_at = None
        attempt.provider_reference = provider_reference
        attempt.failure_reason = None

    def mark_failed(
        self,
        *,
        attempt_id: int,
        failure_reason: str,
        processed_at: datetime,
        next_retry_at: datetime | None,
    ) -> None:
        attempt = self._find(attempt_id)
        attempt.status = "failed"
        attempt.processed_at = processed_at
        attempt.next_retry_at = next_retry_at
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


def test_notification_dispatcher_prepare_dispatch_queues_pending_attempts() -> None:
    """The dispatcher should queue audit rows before any channel executes."""

    repository = FakeDeliveryRepository()
    factory = FakeStrategyFactory(
        strategies={
            "email": FakeStrategy(provider_reference="email-1"),
            "sms": FakeStrategy(provider_reference="sms-1"),
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

    queued_attempts = service.prepare_dispatch(message=message, subscribers=subscribers)

    assert queued_attempts == 2
    assert repository.attempts == [
        RecordedAttempt(
            attempt_id=1,
            message_id=10,
            category_code="sports",
            message_body="Team A won",
            message_created_at=message.created_at,
            user_id=1,
            user_name="Alex",
            user_email="alex@example.com",
            user_phone_number="+15550000001",
            channel_code="email",
            attempt_number=1,
            status="pending",
        ),
        RecordedAttempt(
            attempt_id=2,
            message_id=10,
            category_code="sports",
            message_body="Team A won",
            message_created_at=message.created_at,
            user_id=1,
            user_name="Alex",
            user_email="alex@example.com",
            user_phone_number="+15550000001",
            channel_code="sms",
            attempt_number=1,
            status="pending",
        ),
    ]
    assert factory.strategies["email"].calls == []
    assert factory.strategies["sms"].calls == []


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

    queued_attempts = service.prepare_dispatch(message=message, subscribers=subscribers)
    summary = service.dispatch_pending_attempts(message_id=message.id)

    assert queued_attempts == 2
    assert summary.total_attempts == 2
    assert summary.sent == 1
    assert summary.failed == 1
    assert repository.attempts[0].status == "sent"
    assert repository.attempts[0].provider_reference == "email-1"
    assert repository.attempts[0].processing_started_at is not None
    assert repository.attempts[0].processed_at is not None
    assert repository.attempts[1].status == "failed"
    assert repository.attempts[1].failure_reason == "provider outage"
    assert repository.attempts[1].processing_started_at is not None
    assert repository.attempts[1].processed_at is not None
    assert repository.attempts[1].next_retry_at is None
    assert set(repository.delivered_timestamps) == {1}


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

    queued_attempts = service.prepare_dispatch(message=message, subscribers=subscribers)
    summary = service.dispatch_pending_attempts(message_id=message.id)

    assert queued_attempts == 1
    assert summary.total_attempts == 1
    assert summary.sent == 0
    assert summary.failed == 1
    assert repository.attempts[0].status == "failed"
    assert repository.attempts[0].failure_reason == "missing strategy for push"
    assert repository.attempts[0].processing_started_at is not None
    assert repository.attempts[0].processed_at is not None
    assert repository.delivered_timestamps == {}


def test_notification_dispatcher_skips_subscribers_without_channels() -> None:
    """Subscribers without channel preferences should not create audit attempts."""

    repository = FakeDeliveryRepository()
    service = NotificationDispatcherService(
        attempt_repository=repository,
        strategy_factory=FakeStrategyFactory(
            strategies={"email": FakeStrategy(provider_reference="email-1")}
        ),
    )
    message = PersistedMessage(
        id=12,
        category_code="finance",
        body="Quarterly update",
        created_at=datetime.now(tz=timezone.utc),
    )
    subscribers = [
        ResolvedSubscriber(
            user_id=5,
            name="Casey",
            email="casey@example.com",
            phone_number="+15550000003",
            channel_codes=(),
        )
    ]

    queued_attempts = service.prepare_dispatch(message=message, subscribers=subscribers)
    summary = service.dispatch_pending_attempts(message_id=message.id)

    assert queued_attempts == 0
    assert summary.total_attempts == 0
    assert summary.sent == 0
    assert summary.failed == 0
    assert repository.attempts == []
    assert repository.delivered_timestamps == {}
