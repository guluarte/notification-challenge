"""Transport-agnostic service layer data structures."""

from __future__ import annotations

from collections.abc import Sequence
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
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class UserProfile:
    """User directory record returned by the repository layer."""

    user_id: int
    name: str
    email: str
    phone_number: str


@dataclass(frozen=True, slots=True)
class ResolvedSubscriber:
    """User and channel preferences resolved for message delivery."""

    user_id: int
    name: str
    email: str
    phone_number: str
    channel_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PendingNotificationAttempt:
    """Pending audit row that is ready for channel-specific delivery work."""

    attempt_id: int
    message: PersistedMessage
    subscriber: ResolvedSubscriber
    channel_code: str
    attempt_number: int


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
class MessageDispatchState:
    """Persisted dispatch state for an existing submitted message."""

    total_users: int
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
    idempotency_key: str | None = None
    was_duplicate: bool = False


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
    processing_started_at: datetime | None
    processed_at: datetime | None
    delivered_at: datetime | None
    last_error_at: datetime | None
    next_retry_at: datetime | None
    failure_reason: str | None
    provider_reference: str | None


@dataclass(frozen=True, slots=True)
class NotificationLogPage:
    """Paginated audit-log rows returned by the service layer."""

    items: list[NotificationLogEntry]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class NotificationCatalogItem:
    """Catalog option returned by the repository layer."""

    code: str
    label: str


@dataclass(frozen=True, slots=True)
class NotificationCatalog:
    """Supported message categories and delivery channels."""

    categories: list[NotificationCatalogItem]
    channels: list[NotificationCatalogItem]


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


class CatalogOptionRepositoryProtocol(Protocol):
    """Repository contract for catalog option lists."""

    def list_all(self) -> list[NotificationCatalogItem]:
        """Return every available catalog option."""
        ...


class MessageRepositoryProtocol(Protocol):
    """Repository contract for message persistence."""

    def get_by_idempotency_key(
        self,
        *,
        idempotency_key: str,
    ) -> PersistedMessage | None:
        """Return the message previously created for an idempotency key."""
        ...

    def create(
        self,
        *,
        category_code: str,
        body: str,
        idempotency_key: str | None = None,
    ) -> PersistedMessage:
        """Persist the message and return the repository result."""
        ...


class UserDirectoryRepositoryProtocol(Protocol):
    """Repository contract for loading user directory records."""

    def list_by_ids(self, *, user_ids: Sequence[int]) -> list[UserProfile]:
        """Return user directory records for the given identifiers."""
        ...


class CategorySubscriptionRepositoryProtocol(Protocol):
    """Repository contract for category subscription access."""

    def list_subscribed_user_ids(self, *, category_code: str) -> list[int]:
        """Return user identifiers subscribed to the category."""
        ...


class ChannelPreferenceRepositoryProtocol(Protocol):
    """Repository contract for channel preference access."""

    def list_channel_codes_by_user_ids(
        self,
        *,
        user_ids: Sequence[int],
    ) -> dict[int, tuple[str, ...]]:
        """Return preferred channel codes keyed by user identifier."""
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

    def claim_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> list[PendingNotificationAttempt]:
        """Claim pending attempts that are ready to be processed."""
        ...

    def mark_processing_started(
        self,
        *,
        attempt_id: int,
        processing_started_at: datetime,
    ) -> None:
        """Record when the attempt began execution."""
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

    def mark_failed(
        self,
        *,
        attempt_id: int,
        failure_reason: str,
        processed_at: datetime,
        next_retry_at: datetime | None,
    ) -> None:
        """Mark a delivery attempt as failed."""
        ...

    def summarize_for_message(self, *, message_id: int) -> MessageDispatchState:
        """Return aggregate attempt state for one message."""
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

    def prepare_dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> int:
        """Queue pending attempts for the resolved subscribers."""
        ...

    def dispatch_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> DispatchSummary:
        """Process pending attempts that are ready for delivery."""
        ...

    def summarize_message_dispatch(self, *, message_id: int) -> MessageDispatchState:
        """Return persisted dispatch state for an existing message."""
        ...

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

    def list_recent(self, *, limit: int, offset: int) -> list[NotificationLogEntry]:
        """Return recent notification logs."""
        ...

    def count_all(self) -> int:
        """Return the total number of notification logs."""
        ...
