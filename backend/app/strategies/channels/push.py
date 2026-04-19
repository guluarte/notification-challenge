"""Mock push notification strategy."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from app.models.enums import NotificationChannelCode
from app.services.types import DeliveryResult, PersistedMessage, ResolvedSubscriber

from .base import NotificationStrategy

logger = logging.getLogger(__name__)


class PushNotificationStrategy(NotificationStrategy):
    """Mock push sender used for architecture and testing flows."""

    channel_code = NotificationChannelCode.PUSH.value

    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        """Pretend to send a push notification."""

        logger.info(
            "Dispatching push notification for message_id=%s user_id=%s",
            message.id,
            subscriber.user_id,
        )
        return DeliveryResult(
            provider_reference=f"push-{message.id}-{subscriber.user_id}",
            delivered_at=datetime.now(tz=timezone.utc),
        )
