"""Dispatch notification attempts across configured channel strategies."""

from __future__ import annotations

import logging

from .types import (
    DeliveryAttemptRepositoryProtocol,
    DispatchSummary,
    PersistedMessage,
    ResolvedSubscriber,
    StrategyFactoryProtocol,
)

logger = logging.getLogger(__name__)


class NotificationDispatcherService:
    """Create audit attempts and isolate failures per user and channel."""

    def __init__(
        self,
        *,
        delivery_repository: DeliveryAttemptRepositoryProtocol,
        strategy_factory: StrategyFactoryProtocol,
    ) -> None:
        self.delivery_repository = delivery_repository
        self.strategy_factory = strategy_factory

    def dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> DispatchSummary:
        """Attempt delivery for each user/channel combination."""

        sent = 0
        failed = 0

        for subscriber in subscribers:
            for channel_code in subscriber.channel_codes:
                delivery_id = self.delivery_repository.create_pending_attempt(
                    message=message,
                    subscriber=subscriber,
                    channel_code=channel_code,
                )
                logger.info(
                    "Created delivery attempt id=%s message_id=%s user_id=%s channel=%s",
                    delivery_id,
                    message.id,
                    subscriber.user_id,
                    channel_code,
                )

                try:
                    strategy = self.strategy_factory.get_strategy(channel_code)
                    result = strategy.send(subscriber=subscriber, message=message)
                except Exception as exc:
                    failed += 1
                    self.delivery_repository.mark_failed(
                        delivery_id=delivery_id,
                        failure_reason=str(exc),
                    )
                    logger.exception(
                        "Notification delivery failed for message_id=%s user_id=%s channel=%s",
                        message.id,
                        subscriber.user_id,
                        channel_code,
                    )
                    continue

                sent += 1
                self.delivery_repository.mark_sent(
                    delivery_id=delivery_id,
                    provider_reference=result.provider_reference,
                    delivered_at=result.delivered_at,
                )
                logger.info(
                    "Notification delivery succeeded for message_id=%s user_id=%s channel=%s",
                    message.id,
                    subscriber.user_id,
                    channel_code,
                )

        return DispatchSummary(
            total_attempts=sent + failed,
            sent=sent,
            failed=failed,
        )
