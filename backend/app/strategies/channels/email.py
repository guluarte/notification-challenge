"""Mock email notification strategy."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from app.models.enums import NotificationChannelCode
from app.services.types import DeliveryResult, PersistedMessage, ResolvedSubscriber

from .base import NotificationStrategy

logger = logging.getLogger(__name__)


class EmailNotificationStrategy(NotificationStrategy):
    """Mock email sender used for architecture and testing flows."""

    channel_code = NotificationChannelCode.EMAIL.value

    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        """Pretend to send an email notification."""

        logger.info(
            "Dispatching email notification for message_id=%s user_id=%s",
            message.id,
            subscriber.user_id,
        )
        return DeliveryResult(
            provider_reference=f"email-{message.id}-{subscriber.user_id}",
            delivered_at=datetime.now(tz=timezone.utc),
        )
