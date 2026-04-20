"""Repository access for notification attempt audit rows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from app.models import NotificationAttempt
from app.models.enums import DeliveryStatus
from app.services.types import (
    NotificationLogEntry,
    PendingNotificationAttempt,
    PersistedMessage,
    ResolvedSubscriber,
)

from .base import BaseRepository


class NotificationAttemptRepository(BaseRepository):
    """Create and update notification attempt audit records."""

    def create_pending_attempt(
        self,
        *,
        message: PersistedMessage,
        subscriber: ResolvedSubscriber,
        channel_code: str,
    ) -> int:
        """Persist a pending notification attempt and return its identifier."""

        attempt = NotificationAttempt(
            message_id=message.id,
            user_id=subscriber.user_id,
            channel_code=channel_code,
            category_code=message.category_code,
            message_body=message.body,
            recipient_snapshot=self._snapshot(subscriber),
            attempt_number=1,
            status=DeliveryStatus.PENDING.value,
        )
        self.session.add(attempt)
        self.session.flush()
        return attempt.id

    def list_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> list[PendingNotificationAttempt]:
        """Return pending attempts that are eligible for execution."""

        ready_at = datetime.now(tz=timezone.utc)
        statement = (
            select(NotificationAttempt)
            .options(joinedload(NotificationAttempt.message))
            .where(NotificationAttempt.status == DeliveryStatus.PENDING.value)
            .where(
                or_(
                    NotificationAttempt.next_retry_at.is_(None),
                    NotificationAttempt.next_retry_at <= ready_at,
                )
            )
            .order_by(
                NotificationAttempt.attempted_at.asc(),
                NotificationAttempt.id.asc(),
            )
        )
        if message_id is not None:
            statement = statement.where(NotificationAttempt.message_id == message_id)
        if limit is not None:
            statement = statement.limit(limit)

        attempts = self.session.scalars(statement).all()
        return [self._to_pending_attempt(attempt) for attempt in attempts]

    def mark_processing_started(
        self,
        *,
        attempt_id: int,
        processing_started_at: datetime,
    ) -> None:
        """Record when the pending attempt started running."""

        attempt = self.session.get(NotificationAttempt, attempt_id)
        if attempt is None:
            return

        attempt.processing_started_at = processing_started_at
        self.session.flush()

    def mark_sent(
        self,
        *,
        attempt_id: int,
        provider_reference: str | None,
        delivered_at: datetime,
    ) -> None:
        """Mark a notification attempt as sent."""

        attempt = self.session.get(NotificationAttempt, attempt_id)
        if attempt is None:
            return

        attempt.status = DeliveryStatus.SENT.value
        attempt.provider_reference = provider_reference
        attempt.failure_reason = None
        attempt.last_error_at = None
        attempt.next_retry_at = None
        attempt.delivered_at = delivered_at
        attempt.processed_at = delivered_at
        self.session.flush()

    def mark_failed(
        self,
        *,
        attempt_id: int,
        failure_reason: str,
        processed_at: datetime,
        next_retry_at: datetime | None,
    ) -> None:
        """Mark a notification attempt as failed."""

        attempt = self.session.get(NotificationAttempt, attempt_id)
        if attempt is None:
            return

        attempt.status = DeliveryStatus.FAILED.value
        attempt.failure_reason = failure_reason
        attempt.provider_reference = None
        attempt.delivered_at = None
        attempt.last_error_at = processed_at
        attempt.next_retry_at = next_retry_at
        attempt.processed_at = processed_at
        self.session.flush()

    def list_recent(self) -> list[NotificationLogEntry]:
        """Return notification attempts sorted from newest to oldest."""

        statement = (
            select(NotificationAttempt)
            .options(joinedload(NotificationAttempt.message))
            .order_by(
                NotificationAttempt.attempted_at.desc(),
                NotificationAttempt.id.desc(),
            )
        )
        attempts = self.session.scalars(statement).all()
        return [self._to_log_entry(attempt) for attempt in attempts]

    @staticmethod
    def _snapshot(subscriber: ResolvedSubscriber) -> dict[str, Any]:
        """Return the recipient snapshot stored with the attempt."""

        return {
            "name": subscriber.name,
            "email": subscriber.email,
            "phone_number": subscriber.phone_number,
        }

    @staticmethod
    def _to_pending_attempt(
        attempt: NotificationAttempt,
    ) -> PendingNotificationAttempt:
        """Map an ORM attempt record to the pending dispatch structure."""

        snapshot = attempt.recipient_snapshot
        return PendingNotificationAttempt(
            attempt_id=attempt.id,
            message=PersistedMessage(
                id=attempt.message_id,
                category_code=attempt.category_code,
                body=attempt.message_body,
                created_at=attempt.message.created_at,
            ),
            subscriber=ResolvedSubscriber(
                user_id=attempt.user_id,
                name=str(snapshot.get("name", "")),
                email=str(snapshot.get("email", "")),
                phone_number=str(snapshot.get("phone_number", "")),
                channel_codes=(attempt.channel_code,),
            ),
            channel_code=attempt.channel_code,
            attempt_number=attempt.attempt_number,
        )

    @staticmethod
    def _to_log_entry(attempt: NotificationAttempt) -> NotificationLogEntry:
        """Map an ORM attempt record to the service log structure."""

        snapshot = attempt.recipient_snapshot
        return NotificationLogEntry(
            attempt_id=attempt.id,
            message_id=attempt.message_id,
            category_code=attempt.category_code,
            body=attempt.message_body,
            user_id=attempt.user_id,
            user_name=str(snapshot.get("name", "")),
            user_email=str(snapshot.get("email", "")),
            user_phone_number=str(snapshot.get("phone_number", "")),
            channel_code=attempt.channel_code,
            status=DeliveryStatus(attempt.status),
            attempt_number=attempt.attempt_number,
            attempted_at=attempt.attempted_at,
            processing_started_at=attempt.processing_started_at,
            processed_at=attempt.processed_at,
            delivered_at=attempt.delivered_at,
            last_error_at=attempt.last_error_at,
            next_retry_at=attempt.next_retry_at,
            failure_reason=attempt.failure_reason,
            provider_reference=attempt.provider_reference,
        )
