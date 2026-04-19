"""Repository access for notification attempt audit rows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import NotificationAttempt
from app.models.enums import DeliveryStatus
from app.services.types import (
    NotificationLogEntry,
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
        attempt.delivered_at = delivered_at
        self.session.flush()

    def mark_failed(self, *, attempt_id: int, failure_reason: str) -> None:
        """Mark a notification attempt as failed."""

        attempt = self.session.get(NotificationAttempt, attempt_id)
        if attempt is None:
            return

        attempt.status = DeliveryStatus.FAILED.value
        attempt.failure_reason = failure_reason
        attempt.provider_reference = None
        attempt.delivered_at = None
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
            delivered_at=attempt.delivered_at,
            failure_reason=attempt.failure_reason,
            provider_reference=attempt.provider_reference,
        )
