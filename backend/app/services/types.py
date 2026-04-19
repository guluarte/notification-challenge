"""Transport-agnostic service layer data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.models.enums import DeliveryStatus


@dataclass(frozen=True, slots=True)
class PersistedMessage:
    """Message record returned by the repository layer."""

    id: int
    category_code: str
    body: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ResolvedSubscriber:
    """User and channel preferences resolved for message delivery."""

    user_id: int
    name: str
    email: str
    phone_number: str
    channel_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    """Strategy response for a successful notification attempt."""

    provider_reference: str | None
    delivered_at: datetime


@dataclass(frozen=True, slots=True)
class DispatchSummary:
    """Aggregate dispatch counts for a submitted message."""

    total_attempts: int
    sent: int
    failed: int


@dataclass(frozen=True, slots=True)
class MessageCreationResult:
    """Service result returned after message intake and dispatch."""

    message_id: int
    category_code: str
    body: str
    total_users: int
    total_attempts: int
    sent: int
    failed: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NotificationLogEntry:
    """Audit-log row returned by the repository layer."""

    attempt_id: int
    message_id: int
    category_code: str
    body: str
    user_id: int
    user_name: str
    user_email: str
    user_phone_number: str
    channel_code: str
    status: DeliveryStatus
    attempt_number: int
    attempted_at: datetime
    delivered_at: datetime | None
    failure_reason: str | None
    provider_reference: str | None


class SessionProtocol(Protocol):
    """Behavior the message service requires from a session."""

    def commit(self) -> None:
        """Commit the current unit of work."""
        ...

    def rollback(self) -> None:
        """Roll back the current unit of work."""
        ...


class CategoryRepositoryProtocol(Protocol):
    """Repository contract for category catalog access."""

    def exists(self, category_code: str) -> bool:
        """Return whether the category exists."""
        ...


class MessageRepositoryProtocol(Protocol):
    """Repository contract for message persistence."""

    def create(self, *, category_code: str, body: str) -> PersistedMessage:
        """Persist the message and return the repository result."""
        ...


class SubscriberRepositoryProtocol(Protocol):
    """Repository contract for subscriber resolution."""

    def list_subscribed_users(self, *, category_code: str) -> list[ResolvedSubscriber]:
        """Return subscribed users for a category."""
        ...


class SubscriberResolverProtocol(Protocol):
    """Service contract for subscriber resolution."""

    def resolve_subscribers(self, *, category_code: str) -> list[ResolvedSubscriber]:
        """Resolve subscribers for the category."""
        ...


class DeliveryAttemptRepositoryProtocol(Protocol):
    """Repository contract for delivery attempt persistence."""

    def create_pending_attempt(
        self,
        *,
        message: PersistedMessage,
        subscriber: ResolvedSubscriber,
        channel_code: str,
    ) -> int:
        """Create a pending attempt and return its identifier."""
        ...

    def mark_sent(
        self,
        *,
        attempt_id: int,
        provider_reference: str | None,
        delivered_at: datetime,
    ) -> None:
        """Mark a delivery attempt as sent."""
        ...

    def mark_failed(self, *, attempt_id: int, failure_reason: str) -> None:
        """Mark a delivery attempt as failed."""
        ...


class NotificationStrategyProtocol(Protocol):
    """Strategy contract used by the dispatcher."""

    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        """Send the message through the strategy."""
        ...


class StrategyFactoryProtocol(Protocol):
    """Factory contract for resolving channel strategies."""

    def get_strategy(self, channel_code: str) -> NotificationStrategyProtocol:
        """Return the strategy for a channel code."""
        ...


class NotificationDispatcherProtocol(Protocol):
    """Dispatcher contract used by the message service."""

    def dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> DispatchSummary:
        """Dispatch a message to the resolved subscribers."""
        ...


class NotificationLogRepositoryProtocol(Protocol):
    """Repository contract for audit log listing."""

    def list_recent(self) -> list[NotificationLogEntry]:
        """Return recent notification logs."""
        ...
