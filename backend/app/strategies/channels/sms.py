"""Mock SMS notification strategy."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from app.models.enums import NotificationChannelCode
from app.services.types import DeliveryResult, PersistedMessage, ResolvedSubscriber

from .base import NotificationStrategy

logger = logging.getLogger(__name__)


class SmsNotificationStrategy(NotificationStrategy):
    """Mock SMS sender used for architecture and testing flows."""

    channel_code = NotificationChannelCode.SMS.value

    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        """Pretend to send an SMS notification."""

        logger.info(
            "Dispatching sms notification for message_id=%s user_id=%s",
            message.id,
            subscriber.user_id,
        )
        return DeliveryResult(
            provider_reference=f"sms-{message.id}-{subscriber.user_id}",
            delivered_at=datetime.now(tz=timezone.utc),
        )
