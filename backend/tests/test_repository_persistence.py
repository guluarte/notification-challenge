"""Tests for repository persistence and mapping behavior."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.models import Message, NotificationAttempt
from app.models.enums import DeliveryStatus
from app.repositories.categories import NotificationCategoryRepository
from app.repositories.messages import MessageRepository
from app.repositories.notification_deliveries import NotificationAttemptRepository
from app.services.types import (
    MessageDispatchState,
    NotificationLogEntry,
    NotificationLogFilters,
    PendingNotificationAttempt,
    PersistedMessage,
    ResolvedSubscriber,
)


class FakeTupleResult:
    """Return the configured rows for repository tuple queries."""

    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    def tuples(self) -> FakeTupleResult:
        return self

    def one_or_none(self) -> tuple[Any, ...] | None:
        if len(self.rows) == 0:
            return None
        if len(self.rows) > 1:
            raise AssertionError("Expected at most one row")
        return self.rows[0]

    def __iter__(self) -> Iterator[tuple[Any, ...]]:
        return iter(self.rows)


def _build_message(*, message_id: int, created_at: datetime) -> Message:
    """Build an in-memory message ORM instance for repository mapping tests."""

    return Message(
        id=message_id,
        category_code="sports",
        body="Team A won the championship",
        created_at=created_at,
    )


def _build_attempt(
    *,
    attempt_id: int,
    status: DeliveryStatus,
    created_at: datetime,
) -> NotificationAttempt:
    """Build an in-memory attempt ORM instance for repository mapping tests."""

    message = _build_message(message_id=12, created_at=created_at)
    attempt = NotificationAttempt(
        id=attempt_id,
        message_id=message.id,
        user_id=3,
        channel_code="email",
        category_code="sports",
        message_body=message.body,
        recipient_snapshot={
            "name": "Sam Rivera",
            "email": "sam.rivera@example.com",
            "phone_number": "+15550001003",
        },
        attempt_number=1,
        status=status.value,
        failure_reason=None,
        provider_reference=None,
        attempted_at=created_at,
        processing_started_at=None,
        processed_at=None,
        delivered_at=None,
        last_error_at=None,
        next_retry_at=None,
    )
    attempt.message = message
    return attempt


def test_notification_category_repository_reports_existing_category() -> None:
    """The category repository should treat any scalar row as an existing code."""

    session = Session()
    repository = NotificationCategoryRepository(session)

    with patch.object(session, "scalar", return_value="sports") as scalar_mock:
        exists = repository.exists("sports")

    assert exists is True
    scalar_mock.assert_called_once()
    session.close()


def test_notification_category_repository_reports_missing_category() -> None:
    """The category repository should return false when the query is empty."""

    session = Session()
    repository = NotificationCategoryRepository(session)

    with patch.object(session, "scalar", return_value=None) as scalar_mock:
        exists = repository.exists("weather")

    assert exists is False
    scalar_mock.assert_called_once()
    session.close()


def test_message_repository_creates_and_maps_persisted_message() -> None:
    """The message repository should persist and map the submitted message."""

    created_at = datetime(2026, 4, 20, 19, 15, tzinfo=timezone.utc)
    session = Session()
    repository = MessageRepository(session)
    added_messages: list[Message] = []

    def add_side_effect(instance: object, _warn: bool = True) -> None:
        del _warn
        if not isinstance(instance, Message):
            raise AssertionError("Expected Message")
        added_messages.append(instance)

    def refresh_side_effect(
        instance: object,
        attribute_names: Iterable[str] | None = None,
        with_for_update: object | None = None,
    ) -> None:
        del attribute_names, with_for_update
        if not isinstance(instance, Message):
            raise AssertionError("Expected Message")
        instance.id = 21
        instance.created_at = created_at

    with (
        patch.object(session, "add", side_effect=add_side_effect) as add_mock,
        patch.object(session, "flush") as flush_mock,
        patch.object(
            session,
            "refresh",
            side_effect=refresh_side_effect,
        ) as refresh_mock,
    ):
        result = repository.create(
            category_code="sports",
            body="Team A won the championship",
            idempotency_key="submit-123",
        )

    assert result == PersistedMessage(
        id=21,
        category_code="sports",
        body="Team A won the championship",
        created_at=created_at,
        idempotency_key="submit-123",
    )
    assert len(added_messages) == 1
    assert added_messages[0].category_code == "sports"
    assert added_messages[0].body == "Team A won the championship"
    assert added_messages[0].idempotency_key == "submit-123"
    add_mock.assert_called_once()
    flush_mock.assert_called_once_with()
    refresh_mock.assert_called_once()
    session.close()


def test_message_repository_loads_message_by_idempotency_key() -> None:
    """The message repository should map stored idempotency key matches."""

    created_at = datetime(2026, 4, 20, 19, 25, tzinfo=timezone.utc)
    session = Session()
    repository = MessageRepository(session)
    row = (22, "finance", "Quarterly update", created_at, "submit-456")

    with patch.object(
        session,
        "execute",
        return_value=FakeTupleResult([row]),
    ) as execute_mock:
        result = repository.get_by_idempotency_key(idempotency_key="submit-456")

    assert result == PersistedMessage(
        id=22,
        category_code="finance",
        body="Quarterly update",
        created_at=created_at,
        idempotency_key="submit-456",
    )
    execute_mock.assert_called_once()
    session.close()


def test_message_repository_returns_none_for_missing_idempotency_key() -> None:
    """Missing idempotency keys should return no message."""

    session = Session()
    repository = MessageRepository(session)

    with patch.object(
        session,
        "execute",
        return_value=FakeTupleResult([]),
    ) as execute_mock:
        result = repository.get_by_idempotency_key(idempotency_key="missing")

    assert result is None
    execute_mock.assert_called_once()
    session.close()


def test_notification_attempt_repository_creates_pending_attempt() -> None:
    """Pending attempts should snapshot recipient data when they are queued."""

    created_at = datetime(2026, 4, 20, 19, 30, tzinfo=timezone.utc)
    session = Session()
    repository = NotificationAttemptRepository(session)
    stored_attempts: dict[int, NotificationAttempt] = {}
    message = PersistedMessage(
        id=5,
        category_code="sports",
        body="Team A won the championship",
        created_at=created_at,
    )
    subscriber = ResolvedSubscriber(
        user_id=3,
        name="Sam Rivera",
        email="sam.rivera@example.com",
        phone_number="+15550001003",
        channel_codes=("email", "push"),
    )

    def add_side_effect(instance: object, _warn: bool = True) -> None:
        del _warn
        if not isinstance(instance, NotificationAttempt):
            raise AssertionError("Expected NotificationAttempt")
        instance.id = 1
        instance.attempted_at = created_at
        stored_attempts[instance.id] = instance

    with (
        patch.object(session, "add", side_effect=add_side_effect) as add_mock,
        patch.object(session, "flush") as flush_mock,
    ):
        attempt_id = repository.create_pending_attempt(
            message=message,
            subscriber=subscriber,
            channel_code="email",
        )

    assert attempt_id == 1
    stored_attempt = stored_attempts[attempt_id]
    assert stored_attempt.message_id == 5
    assert stored_attempt.user_id == 3
    assert stored_attempt.channel_code == "email"
    assert stored_attempt.category_code == "sports"
    assert stored_attempt.message_body == "Team A won the championship"
    assert stored_attempt.attempt_number == 1
    assert stored_attempt.status == DeliveryStatus.PENDING.value
    assert stored_attempt.recipient_snapshot == {
        "name": "Sam Rivera",
        "email": "sam.rivera@example.com",
        "phone_number": "+15550001003",
    }
    add_mock.assert_called_once()
    flush_mock.assert_called_once_with()
    session.close()


def test_notification_attempt_repository_marks_sent_attempts() -> None:
    """Sent attempts should record delivery and clear failure metadata."""

    created_at = datetime(2026, 4, 20, 19, 45, tzinfo=timezone.utc)
    session = Session()
    repository = NotificationAttemptRepository(session)
    attempt = _build_attempt(
        attempt_id=7,
        status=DeliveryStatus.PENDING,
        created_at=created_at,
    )
    processing_started_at = datetime(2026, 4, 20, 19, 46, tzinfo=timezone.utc)
    delivered_at = datetime(2026, 4, 20, 19, 47, tzinfo=timezone.utc)

    with (
        patch.object(session, "get", return_value=attempt) as get_mock,
        patch.object(session, "flush") as flush_mock,
    ):
        repository.mark_processing_started(
            attempt_id=7,
            processing_started_at=processing_started_at,
        )
        repository.mark_sent(
            attempt_id=7,
            provider_reference="email-12-3",
            delivered_at=delivered_at,
        )

    assert attempt.processing_started_at == processing_started_at
    assert attempt.status == DeliveryStatus.SENT.value
    assert attempt.provider_reference == "email-12-3"
    assert attempt.failure_reason is None
    assert attempt.last_error_at is None
    assert attempt.next_retry_at is None
    assert attempt.delivered_at == delivered_at
    assert attempt.processed_at == delivered_at
    assert get_mock.call_count == 2
    assert flush_mock.call_count == 2
    session.close()


def test_notification_attempt_repository_marks_failed_attempts() -> None:
    """Failed attempts should retain retry-related failure metadata."""

    created_at = datetime(2026, 4, 20, 20, 0, tzinfo=timezone.utc)
    processed_at = datetime(2026, 4, 20, 20, 1, tzinfo=timezone.utc)
    next_retry_at = datetime(2026, 4, 20, 20, 31, tzinfo=timezone.utc)
    session = Session()
    repository = NotificationAttemptRepository(session)
    attempt = _build_attempt(
        attempt_id=8,
        status=DeliveryStatus.PENDING,
        created_at=created_at,
    )

    with (
        patch.object(session, "get", return_value=attempt) as get_mock,
        patch.object(session, "flush") as flush_mock,
    ):
        repository.mark_failed(
            attempt_id=8,
            failure_reason="provider outage",
            processed_at=processed_at,
            next_retry_at=next_retry_at,
        )

    assert attempt.status == DeliveryStatus.FAILED.value
    assert attempt.failure_reason == "provider outage"
    assert attempt.provider_reference is None
    assert attempt.delivered_at is None
    assert attempt.last_error_at == processed_at
    assert attempt.next_retry_at == next_retry_at
    assert attempt.processed_at == processed_at
    get_mock.assert_called_once()
    flush_mock.assert_called_once_with()
    session.close()


def test_notification_attempt_repository_maps_pending_attempts() -> None:
    """Pending attempt rows should map into dispatch-ready service objects."""

    created_at = datetime(2026, 4, 20, 20, 15, tzinfo=timezone.utc)
    pending_attempt = _build_attempt(
        attempt_id=9,
        status=DeliveryStatus.PENDING,
        created_at=created_at,
    )
    session = Session()
    repository = NotificationAttemptRepository(session)

    row = (
        pending_attempt.id,
        pending_attempt.message_id,
        pending_attempt.category_code,
        pending_attempt.message_body,
        created_at,
        pending_attempt.user_id,
        pending_attempt.recipient_snapshot,
        pending_attempt.channel_code,
        pending_attempt.attempt_number,
    )

    with patch.object(
        session,
        "execute",
        return_value=FakeTupleResult([row]),
    ) as execute_mock:
        attempts = repository.claim_pending_attempts(message_id=12, limit=10)

    assert attempts == [
        PendingNotificationAttempt(
            attempt_id=9,
            message=PersistedMessage(
                id=12,
                category_code="sports",
                body="Team A won the championship",
                created_at=created_at,
            ),
            subscriber=ResolvedSubscriber(
                user_id=3,
                name="Sam Rivera",
                email="sam.rivera@example.com",
                phone_number="+15550001003",
                channel_codes=("email",),
            ),
            channel_code="email",
            attempt_number=1,
        )
    ]
    execute_mock.assert_called_once()
    statement = execute_mock.call_args.args[0]
    compiled_statement = str(statement.compile(dialect=postgresql.dialect())).upper()
    assert "FOR UPDATE" in compiled_statement
    assert "SKIP LOCKED" in compiled_statement
    session.close()


def test_notification_attempt_repository_maps_recent_logs() -> None:
    """Recent attempt rows should map into API-facing log entries."""

    created_at = datetime(2026, 4, 20, 20, 30, tzinfo=timezone.utc)
    delivered_at = datetime(2026, 4, 20, 20, 31, tzinfo=timezone.utc)
    attempt = _build_attempt(
        attempt_id=10,
        status=DeliveryStatus.SENT,
        created_at=created_at,
    )
    attempt.processing_started_at = created_at
    attempt.processed_at = delivered_at
    attempt.delivered_at = delivered_at
    attempt.provider_reference = "email-12-3"
    session = Session()
    repository = NotificationAttemptRepository(session)

    row = (
        attempt.id,
        attempt.message_id,
        attempt.category_code,
        attempt.message_body,
        attempt.user_id,
        attempt.recipient_snapshot,
        attempt.channel_code,
        attempt.status,
        attempt.attempt_number,
        attempt.attempted_at,
        attempt.processing_started_at,
        attempt.processed_at,
        attempt.delivered_at,
        attempt.last_error_at,
        attempt.next_retry_at,
        attempt.failure_reason,
        attempt.provider_reference,
    )

    with patch.object(
        session,
        "execute",
        return_value=FakeTupleResult([row]),
    ) as execute_mock:
        logs = repository.list_recent(
            limit=10,
            offset=20,
            filters=NotificationLogFilters(),
        )

    assert logs == [
        NotificationLogEntry(
            attempt_id=10,
            message_id=12,
            category_code="sports",
            body="Team A won the championship",
            user_id=3,
            user_name="Sam Rivera",
            user_email="sam.rivera@example.com",
            user_phone_number="+15550001003",
            channel_code="email",
            status=DeliveryStatus.SENT,
            attempt_number=1,
            attempted_at=created_at,
            processing_started_at=created_at,
            processed_at=delivered_at,
            delivered_at=delivered_at,
            last_error_at=None,
            next_retry_at=None,
            failure_reason=None,
            provider_reference="email-12-3",
        )
    ]
    execute_mock.assert_called_once()
    session.close()


def test_notification_attempt_repository_applies_log_search_filters() -> None:
    """Log list queries should support exact filters and text search."""

    session = Session()
    repository = NotificationAttemptRepository(session)
    filters = NotificationLogFilters(
        category_code="sports",
        channel_code="email",
        status=DeliveryStatus.FAILED,
        message_id=12,
        user_id=3,
        search="Sam Rivera",
    )

    with patch.object(
        session,
        "execute",
        return_value=FakeTupleResult([]),
    ) as execute_mock:
        logs = repository.list_recent(limit=10, offset=0, filters=filters)

    assert logs == []
    execute_mock.assert_called_once()
    statement = execute_mock.call_args.args[0]
    compiled_statement = str(statement.compile(dialect=postgresql.dialect())).upper()
    assert "NOTIFICATION_ATTEMPTS.CATEGORY_CODE" in compiled_statement
    assert "NOTIFICATION_ATTEMPTS.CHANNEL_CODE" in compiled_statement
    assert "NOTIFICATION_ATTEMPTS.STATUS" in compiled_statement
    assert "NOTIFICATION_ATTEMPTS.MESSAGE_ID" in compiled_statement
    assert "NOTIFICATION_ATTEMPTS.USER_ID" in compiled_statement
    assert "ILIKE" in compiled_statement
    assert "RECIPIENT_SNAPSHOT" in compiled_statement
    session.close()


def test_notification_attempt_repository_counts_logs() -> None:
    """The repository should expose the total audit row count for pagination."""

    session = Session()
    repository = NotificationAttemptRepository(session)

    with patch.object(session, "scalar", return_value=42) as scalar_mock:
        total = repository.count_all(
            filters=NotificationLogFilters(status=DeliveryStatus.SENT)
        )

    assert total == 42
    scalar_mock.assert_called_once()
    session.close()


def test_notification_attempt_repository_summarizes_message_dispatch() -> None:
    """The repository should aggregate existing attempt state for replayed posts."""

    session = Session()
    repository = NotificationAttemptRepository(session)

    with patch.object(session, "scalar", side_effect=[5, 2, 4, 1]) as scalar_mock:
        summary = repository.summarize_for_message(message_id=12)

    assert summary == MessageDispatchState(
        total_users=2,
        total_attempts=5,
        sent=4,
        failed=1,
    )
    assert scalar_mock.call_count == 4
    session.close()
