"""Repository access for notification delivery audit rows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import NotificationDelivery
from app.models.enums import DeliveryStatus
from app.services.types import (
    NotificationLogEntry,
    PersistedMessage,
    ResolvedSubscriber,
)

from .base import BaseRepository


class NotificationDeliveryRepository(BaseRepository):
    """Create and update notification delivery audit records."""

    def create_pending_attempt(
        self,
        *,
        message: PersistedMessage,
        subscriber: ResolvedSubscriber,
        channel_code: str,
    ) -> int:
        """Persist a pending delivery attempt and return its identifier."""

        delivery = NotificationDelivery(
            message_id=message.id,
            user_id=subscriber.user_id,
            channel_code=channel_code,
            category_code=message.category_code,
            message_body=message.body,
            recipient_snapshot=self._snapshot(subscriber),
            attempt_number=1,
            status=DeliveryStatus.PENDING.value,
        )
        self.session.add(delivery)
        self.session.flush()
        return delivery.id

    def mark_sent(
        self,
        *,
        delivery_id: int,
        provider_reference: str | None,
        delivered_at: datetime,
    ) -> None:
        """Mark a delivery attempt as sent."""

        delivery = self.session.get(NotificationDelivery, delivery_id)
        if delivery is None:
            return

        delivery.status = DeliveryStatus.SENT.value
        delivery.provider_reference = provider_reference
        delivery.failure_reason = None
        delivery.delivered_at = delivered_at
        self.session.flush()

    def mark_failed(self, *, delivery_id: int, failure_reason: str) -> None:
        """Mark a delivery attempt as failed."""

        delivery = self.session.get(NotificationDelivery, delivery_id)
        if delivery is None:
            return

        delivery.status = DeliveryStatus.FAILED.value
        delivery.failure_reason = failure_reason
        delivery.provider_reference = None
        delivery.delivered_at = None
        self.session.flush()

    def list_recent(self) -> list[NotificationLogEntry]:
        """Return delivery attempts sorted from newest to oldest."""

        statement = (
            select(NotificationDelivery)
            .options(joinedload(NotificationDelivery.message))
            .order_by(
                NotificationDelivery.attempted_at.desc(),
                NotificationDelivery.id.desc(),
            )
        )
        deliveries = self.session.scalars(statement).all()
        return [self._to_log_entry(delivery) for delivery in deliveries]

    @staticmethod
    def _snapshot(subscriber: ResolvedSubscriber) -> dict[str, Any]:
        """Return the audit snapshot stored with the attempt."""

        return {
            "name": subscriber.name,
            "email": subscriber.email,
            "phone_number": subscriber.phone_number,
        }

    @staticmethod
    def _to_log_entry(delivery: NotificationDelivery) -> NotificationLogEntry:
        """Map an ORM delivery record to the service log structure."""

        snapshot = delivery.recipient_snapshot
        return NotificationLogEntry(
            delivery_id=delivery.id,
            message_id=delivery.message_id,
            category_code=delivery.category_code,
            body=delivery.message_body,
            user_id=delivery.user_id,
            user_name=str(snapshot.get("name", "")),
            user_email=str(snapshot.get("email", "")),
            user_phone_number=str(snapshot.get("phone_number", "")),
            channel_code=delivery.channel_code,
            status=DeliveryStatus(delivery.status),
            attempt_number=delivery.attempt_number,
            attempted_at=delivery.attempted_at,
            delivered_at=delivery.delivered_at,
            failure_reason=delivery.failure_reason,
            provider_reference=delivery.provider_reference,
        )
