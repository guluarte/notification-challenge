"""Tests for message intake orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    IdempotencyConflictError,
    InfrastructureError,
    ServiceUnavailableError,
)
from app.services.message_service import MessageService
from app.services.types import (
    DispatchSummary,
    MessageDispatchState,
    MessageCreationResult,
    PersistedMessage,
    ResolvedSubscriber,
)


class FakeSession:
    """Minimal session double that records commit and rollback calls."""

    def __init__(self, *, commit_error: SQLAlchemyError | None = None) -> None:
        self.commit_error = commit_error
        self.commit_called = False
        self.rollback_called = False

    def commit(self) -> None:
        self.commit_called = True
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self) -> None:
        self.rollback_called = True


class FakeCategoryRepository:
    """Category repository double."""

    def __init__(
        self,
        *,
        exists: bool,
        error: SQLAlchemyError | None = None,
    ) -> None:
        self._exists = exists
        self.error = error

    def exists(self, category_code: str) -> bool:
        del category_code
        if self.error is not None:
            raise self.error
        return self._exists


class FakeMessageRepository:
    """Message repository double that returns a known persisted message."""

    def __init__(
        self,
        persisted_message: PersistedMessage,
        *,
        existing_by_key: dict[str, PersistedMessage] | None = None,
        existing_by_key_results: list[PersistedMessage | None] | None = None,
        create_error: SQLAlchemyError | None = None,
    ) -> None:
        self.persisted_message = persisted_message
        self.existing_by_key = existing_by_key or {}
        self.existing_by_key_results = existing_by_key_results
        self.create_error = create_error
        self.calls: list[tuple[str, str, str | None]] = []
        self.get_by_idempotency_key_calls: list[str] = []

    def get_by_idempotency_key(
        self,
        *,
        idempotency_key: str,
    ) -> PersistedMessage | None:
        self.get_by_idempotency_key_calls.append(idempotency_key)
        if self.existing_by_key_results is not None:
            return self.existing_by_key_results.pop(0)
        return self.existing_by_key.get(idempotency_key)

    def create(
        self,
        *,
        category_code: str,
        body: str,
        idempotency_key: str | None = None,
    ) -> PersistedMessage:
        self.calls.append((category_code, body, idempotency_key))
        if self.create_error is not None:
            raise self.create_error
        return self.persisted_message


class FakeSubscriberResolver:
    """Subscriber resolver double."""

    def __init__(self, *, count: int) -> None:
        self.count = count
        self.calls: list[str] = []
        self.subscribers = [
            ResolvedSubscriber(
                user_id=index + 1,
                name=f"User {index + 1}",
                email=f"user{index + 1}@example.com",
                phone_number=f"+1555000000{index + 1}",
                channel_codes=("email",),
            )
            for index in range(count)
        ]

    def resolve_subscribers(self, *, category_code: str) -> list[ResolvedSubscriber]:
        self.calls.append(category_code)
        return self.subscribers


class FakeNotificationDispatcher:
    """Dispatcher double returning a fixed summary."""

    def __init__(self, *, queued_attempts: int, summary: DispatchSummary) -> None:
        self.queued_attempts = queued_attempts
        self.summary = summary
        self.dispatch_state = MessageDispatchState(
            total_users=0,
            total_attempts=summary.total_attempts,
            sent=summary.sent,
            failed=summary.failed,
        )
        self.prepare_calls: list[tuple[PersistedMessage, list[ResolvedSubscriber]]] = []
        self.dispatch_calls: list[tuple[int | None, int | None]] = []
        self.summarize_calls: list[int] = []

    def prepare_dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> int:
        self.prepare_calls.append((message, subscribers))
        return self.queued_attempts

    def dispatch_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> DispatchSummary:
        self.dispatch_calls.append((message_id, limit))
        return self.summary

    def summarize_message_dispatch(self, *, message_id: int) -> MessageDispatchState:
        self.summarize_calls.append(message_id)
        return self.dispatch_state

    def dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> DispatchSummary:
        del message, subscribers
        return self.summary


def _unique_key_error() -> IntegrityError:
    """Return an integrity error shaped like a duplicate key failure."""

    return IntegrityError(
        "INSERT INTO messages",
        {},
        Exception("duplicate key value violates unique constraint"),
    )


def test_message_service_commits_successful_dispatch() -> None:
    """The service should commit after persisting and dispatching a message."""

    session = FakeSession()
    message = PersistedMessage(
        id=5,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
    )
    message_repository = FakeMessageRepository(message)
    subscriber_resolver = FakeSubscriberResolver(count=2)
    dispatcher = FakeNotificationDispatcher(
        queued_attempts=3,
        summary=DispatchSummary(total_attempts=3, sent=2, failed=1),
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=subscriber_resolver,
        notification_dispatcher=dispatcher,
    )

    result = service.create_message(category_code="sports", body="Team A won")

    assert result == MessageCreationResult(
        message_id=5,
        category_code="sports",
        body="Team A won",
        total_users=2,
        total_attempts=3,
        sent=2,
        failed=1,
        created_at=message.created_at,
    )
    assert session.commit_called is True
    assert session.rollback_called is False
    assert message_repository.calls == [("sports", "Team A won", None)]
    assert subscriber_resolver.calls == ["sports"]
    assert dispatcher.prepare_calls == [(message, subscriber_resolver.subscribers)]
    assert dispatcher.dispatch_calls == [(5, None)]


def test_message_service_replays_existing_message_for_matching_idempotency_key() -> (
    None
):
    """Duplicate submissions should return existing dispatch state without fan-out."""

    session = FakeSession()
    existing_message = PersistedMessage(
        id=6,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
        idempotency_key="submit-123",
    )
    new_message = PersistedMessage(
        id=7,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
    )
    message_repository = FakeMessageRepository(
        new_message,
        existing_by_key={"submit-123": existing_message},
    )
    subscriber_resolver = FakeSubscriberResolver(count=2)
    dispatcher = FakeNotificationDispatcher(
        queued_attempts=0,
        summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
    )
    dispatcher.dispatch_state = MessageDispatchState(
        total_users=2,
        total_attempts=3,
        sent=2,
        failed=1,
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=subscriber_resolver,
        notification_dispatcher=dispatcher,
    )

    result = service.create_message(
        category_code="sports",
        body="Team A won",
        idempotency_key=" submit-123 ",
    )

    assert result == MessageCreationResult(
        message_id=6,
        category_code="sports",
        body="Team A won",
        total_users=2,
        total_attempts=3,
        sent=2,
        failed=1,
        created_at=existing_message.created_at,
        idempotency_key="submit-123",
        was_duplicate=True,
    )
    assert session.commit_called is False
    assert session.rollback_called is False
    assert message_repository.get_by_idempotency_key_calls == ["submit-123"]
    assert message_repository.calls == []
    assert subscriber_resolver.calls == []
    assert dispatcher.prepare_calls == []
    assert dispatcher.dispatch_calls == []
    assert dispatcher.summarize_calls == [6]


def test_message_service_rejects_idempotency_key_reuse_for_different_payload() -> None:
    """An idempotency key cannot be reused for a different category or body."""

    session = FakeSession()
    existing_message = PersistedMessage(
        id=6,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
        idempotency_key="submit-123",
    )
    message_repository = FakeMessageRepository(
        PersistedMessage(
            id=7,
            category_code="sports",
            body="Quarterly update",
            created_at=datetime.now(tz=timezone.utc),
        ),
        existing_by_key={"submit-123": existing_message},
    )
    dispatcher = FakeNotificationDispatcher(
        queued_attempts=0,
        summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=FakeSubscriberResolver(count=2),
        notification_dispatcher=dispatcher,
    )

    try:
        service.create_message(
            category_code="finance",
            body="Quarterly update",
            idempotency_key="submit-123",
        )
    except IdempotencyConflictError as exc:
        assert (
            exc.detail
            == "The idempotency key has already been used for a different message."
        )
    else:
        raise AssertionError("Expected IdempotencyConflictError")

    assert session.commit_called is False
    assert session.rollback_called is False
    assert message_repository.calls == []
    assert dispatcher.prepare_calls == []
    assert dispatcher.dispatch_calls == []


def test_message_service_persists_idempotency_key_for_new_submission() -> None:
    """New submissions should store normalized idempotency keys on the message."""

    session = FakeSession()
    message = PersistedMessage(
        id=15,
        category_code="finance",
        body="Quarterly update",
        created_at=datetime.now(tz=timezone.utc),
        idempotency_key="submit-456",
    )
    message_repository = FakeMessageRepository(message)
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=FakeSubscriberResolver(count=0),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=0,
            summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
        ),
    )

    result = service.create_message(
        category_code="finance",
        body="Quarterly update",
        idempotency_key=" submit-456 ",
    )

    assert result.idempotency_key == "submit-456"
    assert result.was_duplicate is False
    assert message_repository.get_by_idempotency_key_calls == ["submit-456"]
    assert message_repository.calls == [("finance", "Quarterly update", "submit-456")]


def test_message_service_replays_after_concurrent_idempotency_insert() -> None:
    """A duplicate-key race should reload and replay the winning message."""

    session = FakeSession()
    existing_message = PersistedMessage(
        id=18,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
        idempotency_key="submit-789",
    )
    message_repository = FakeMessageRepository(
        PersistedMessage(
            id=19,
            category_code="sports",
            body="Team A won",
            created_at=datetime.now(tz=timezone.utc),
        ),
        existing_by_key_results=[None, existing_message],
        create_error=_unique_key_error(),
    )
    dispatcher = FakeNotificationDispatcher(
        queued_attempts=0,
        summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
    )
    dispatcher.dispatch_state = MessageDispatchState(
        total_users=2,
        total_attempts=5,
        sent=5,
        failed=0,
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=FakeSubscriberResolver(count=2),
        notification_dispatcher=dispatcher,
    )

    result = service.create_message(
        category_code="sports",
        body="Team A won",
        idempotency_key="submit-789",
    )

    assert result == MessageCreationResult(
        message_id=18,
        category_code="sports",
        body="Team A won",
        total_users=2,
        total_attempts=5,
        sent=5,
        failed=0,
        created_at=existing_message.created_at,
        idempotency_key="submit-789",
        was_duplicate=True,
    )
    assert session.rollback_called is True
    assert session.commit_called is False
    assert message_repository.get_by_idempotency_key_calls == [
        "submit-789",
        "submit-789",
    ]
    assert message_repository.calls == [("sports", "Team A won", "submit-789")]
    assert dispatcher.prepare_calls == []
    assert dispatcher.dispatch_calls == []
    assert dispatcher.summarize_calls == [18]


def test_message_service_conflicts_after_concurrent_idempotency_insert_reuse() -> None:
    """A raced duplicate with a different payload should still return a conflict."""

    session = FakeSession()
    existing_message = PersistedMessage(
        id=18,
        category_code="sports",
        body="Team A won",
        created_at=datetime.now(tz=timezone.utc),
        idempotency_key="submit-789",
    )
    message_repository = FakeMessageRepository(
        PersistedMessage(
            id=19,
            category_code="finance",
            body="Quarterly update",
            created_at=datetime.now(tz=timezone.utc),
        ),
        existing_by_key_results=[None, existing_message],
        create_error=_unique_key_error(),
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=FakeSubscriberResolver(count=2),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=0,
            summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
        ),
    )

    try:
        service.create_message(
            category_code="finance",
            body="Quarterly update",
            idempotency_key="submit-789",
        )
    except IdempotencyConflictError as exc:
        assert (
            exc.detail
            == "The idempotency key has already been used for a different message."
        )
    else:
        raise AssertionError("Expected IdempotencyConflictError")

    assert session.rollback_called is True
    assert session.commit_called is False
    assert message_repository.get_by_idempotency_key_calls == [
        "submit-789",
        "submit-789",
    ]
    assert message_repository.calls == [("finance", "Quarterly update", "submit-789")]


def test_message_service_keeps_infrastructure_error_when_insert_conflict_missing() -> (
    None
):
    """Integrity errors without a reloadable idempotent message remain infrastructure failures."""

    session = FakeSession()
    message_repository = FakeMessageRepository(
        PersistedMessage(
            id=19,
            category_code="sports",
            body="Team A won",
            created_at=datetime.now(tz=timezone.utc),
        ),
        existing_by_key_results=[None, None],
        create_error=_unique_key_error(),
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=message_repository,
        subscriber_resolver=FakeSubscriberResolver(count=2),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=0,
            summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
        ),
    )

    try:
        service.create_message(
            category_code="sports",
            body="Team A won",
            idempotency_key="submit-789",
        )
    except InfrastructureError as exc:
        assert exc.detail == "The message could not be persisted."
    else:
        raise AssertionError("Expected InfrastructureError")

    assert session.rollback_called is True
    assert session.commit_called is False
    assert message_repository.get_by_idempotency_key_calls == [
        "submit-789",
        "submit-789",
    ]


def test_message_service_returns_zero_attempts_for_empty_subscriber_list() -> None:
    """Messages without subscribers should still be persisted successfully."""

    session = FakeSession()
    message = PersistedMessage(
        id=8,
        category_code="finance",
        body="Quarterly update",
        created_at=datetime.now(tz=timezone.utc),
    )
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=FakeMessageRepository(message),
        subscriber_resolver=FakeSubscriberResolver(count=0),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=0,
            summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
        ),
    )

    result = service.create_message(
        category_code="finance",
        body="Quarterly update",
    )

    assert result.total_users == 0
    assert result.total_attempts == 0
    assert result.sent == 0
    assert result.failed == 0
    assert session.commit_called is True


def test_message_service_raises_service_unavailable_when_category_catalog_is_missing() -> (
    None
):
    """The service should fail fast when the category catalog is unavailable."""

    session = FakeSession()
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=False),
        message_repository=FakeMessageRepository(
            PersistedMessage(
                id=1,
                category_code="movies",
                body="ignored",
                created_at=datetime.now(tz=timezone.utc),
            )
        ),
        subscriber_resolver=FakeSubscriberResolver(count=0),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=0,
            summary=DispatchSummary(total_attempts=0, sent=0, failed=0),
        ),
    )

    try:
        service.create_message(category_code="movies", body="Premiere tonight")
    except ServiceUnavailableError as exc:
        assert exc.detail == "The notification category catalog is unavailable."
    else:
        raise AssertionError("Expected ServiceUnavailableError")

    assert session.commit_called is False
    assert session.rollback_called is False


def test_message_service_rolls_back_when_commit_fails() -> None:
    """A failed commit should roll back and surface an infrastructure error."""

    session = FakeSession(commit_error=SQLAlchemyError("commit failed"))
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=FakeMessageRepository(
            PersistedMessage(
                id=9,
                category_code="sports",
                body="Playoffs",
                created_at=datetime.now(tz=timezone.utc),
            )
        ),
        subscriber_resolver=FakeSubscriberResolver(count=1),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=1,
            summary=DispatchSummary(total_attempts=1, sent=1, failed=0),
        ),
    )

    try:
        service.create_message(category_code="sports", body="Playoffs")
    except InfrastructureError as exc:
        assert exc.detail == "The message could not be persisted."
    else:
        raise AssertionError("Expected InfrastructureError")

    assert session.commit_called is True
    assert session.rollback_called is True


def test_message_service_wraps_category_lookup_database_errors() -> None:
    """A catalog query failure should roll back and use the standard error contract."""

    session = FakeSession()
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(
            exists=True,
            error=SQLAlchemyError("catalog unavailable"),
        ),
        message_repository=FakeMessageRepository(
            PersistedMessage(
                id=9,
                category_code="sports",
                body="Playoffs",
                created_at=datetime.now(tz=timezone.utc),
            )
        ),
        subscriber_resolver=FakeSubscriberResolver(count=1),
        notification_dispatcher=FakeNotificationDispatcher(
            queued_attempts=1,
            summary=DispatchSummary(total_attempts=1, sent=1, failed=0),
        ),
    )

    try:
        service.create_message(category_code="sports", body="Playoffs")
    except InfrastructureError as exc:
        assert exc.detail == "The message could not be persisted."
    else:
        raise AssertionError("Expected InfrastructureError")

    assert session.commit_called is False
    assert session.rollback_called is True


def test_message_service_can_queue_attempts_without_dispatching_them() -> None:
    """The service should support persisting pending attempts for later workers."""

    session = FakeSession()
    message = PersistedMessage(
        id=13,
        category_code="movies",
        body="Premiere tonight",
        created_at=datetime.now(tz=timezone.utc),
    )
    dispatcher = FakeNotificationDispatcher(
        queued_attempts=2,
        summary=DispatchSummary(total_attempts=2, sent=2, failed=0),
    )
    subscriber_resolver = FakeSubscriberResolver(count=2)
    service = MessageService(
        session=session,
        category_repository=FakeCategoryRepository(exists=True),
        message_repository=FakeMessageRepository(message),
        subscriber_resolver=subscriber_resolver,
        notification_dispatcher=dispatcher,
    )

    result = service.create_message(
        category_code="movies",
        body="Premiere tonight",
        dispatch_immediately=False,
    )

    assert result == MessageCreationResult(
        message_id=13,
        category_code="movies",
        body="Premiere tonight",
        total_users=2,
        total_attempts=2,
        sent=0,
        failed=0,
        created_at=message.created_at,
    )
    assert session.commit_called is True
    assert session.rollback_called is False
    assert dispatcher.prepare_calls == [(message, subscriber_resolver.subscribers)]
    assert dispatcher.dispatch_calls == []
