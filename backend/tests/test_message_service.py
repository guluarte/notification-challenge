"""Tests for message intake orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import InfrastructureError, ServiceUnavailableError
from app.services.message_service import MessageService
from app.services.types import (
    DispatchSummary,
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

    def __init__(self, *, exists: bool) -> None:
        self._exists = exists

    def exists(self, category_code: str) -> bool:
        del category_code
        return self._exists


class FakeMessageRepository:
    """Message repository double that returns a known persisted message."""

    def __init__(self, persisted_message: PersistedMessage) -> None:
        self.persisted_message = persisted_message
        self.calls: list[tuple[str, str]] = []

    def create(self, *, category_code: str, body: str) -> PersistedMessage:
        self.calls.append((category_code, body))
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

    def __init__(self, summary: DispatchSummary) -> None:
        self.summary = summary
        self.calls: list[tuple[PersistedMessage, list[ResolvedSubscriber]]] = []

    def dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> DispatchSummary:
        self.calls.append((message, subscribers))
        return self.summary


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
        DispatchSummary(total_attempts=3, sent=2, failed=1)
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
    assert message_repository.calls == [("sports", "Team A won")]
    assert subscriber_resolver.calls == ["sports"]
    assert dispatcher.calls == [(message, subscriber_resolver.subscribers)]


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
            DispatchSummary(total_attempts=0, sent=0, failed=0)
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
            DispatchSummary(total_attempts=0, sent=0, failed=0)
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
            DispatchSummary(total_attempts=1, sent=1, failed=0)
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
