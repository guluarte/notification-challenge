"""Dispatch notification attempts across configured channel strategies."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from .types import (
    DeliveryAttemptRepositoryProtocol,
    DispatchSummary,
    MessageDispatchState,
    PendingNotificationAttempt,
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
        attempt_repository: DeliveryAttemptRepositoryProtocol,
        strategy_factory: StrategyFactoryProtocol,
    ) -> None:
        self.attempt_repository = attempt_repository
        self.strategy_factory = strategy_factory

    def prepare_dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> int:
        """Queue one pending attempt per user/channel combination."""

        queued_attempts = 0

        for subscriber in subscribers:
            if len(subscriber.channel_codes) == 0:
                logger.info(
                    "Skipping subscriber user_id=%s for message_id=%s because no channels are configured",
                    subscriber.user_id,
                    message.id,
                )
                continue

            for channel_code in subscriber.channel_codes:
                attempt_id = self.attempt_repository.create_pending_attempt(
                    message=message,
                    subscriber=subscriber,
                    channel_code=channel_code,
                )
                queued_attempts += 1
                logger.info(
                    "Queued notification attempt id=%s message_id=%s user_id=%s channel=%s",
                    attempt_id,
                    message.id,
                    subscriber.user_id,
                    channel_code,
                )

        return queued_attempts

    def dispatch_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> DispatchSummary:
        """Deliver ready pending attempts from the audit table."""

        sent = 0
        failed = 0
        pending_attempts = self.attempt_repository.claim_pending_attempts(
            message_id=message_id,
            limit=limit,
        )
        logger.info(
            "Claimed pending notification attempts message_id=%s limit=%s count=%s",
            message_id,
            limit,
            len(pending_attempts),
        )

        for pending_attempt in pending_attempts:
            if self._deliver_attempt(pending_attempt=pending_attempt):
                sent += 1
            else:
                failed += 1

        return DispatchSummary(
            total_attempts=len(pending_attempts),
            sent=sent,
            failed=failed,
        )

    def summarize_message_dispatch(self, *, message_id: int) -> MessageDispatchState:
        """Return the persisted dispatch state for an existing message."""

        state = self.attempt_repository.summarize_for_message(message_id=message_id)
        logger.info(
            "Loaded idempotent dispatch state for message_id=%s users=%s attempts=%s sent=%s failed=%s",
            message_id,
            state.total_users,
            state.total_attempts,
            state.sent,
            state.failed,
        )
        return state

    def dispatch(
        self,
        *,
        message: PersistedMessage,
        subscribers: list[ResolvedSubscriber],
    ) -> DispatchSummary:
        """Queue and deliver notification attempts in-process."""

        queued_attempts = self.prepare_dispatch(
            message=message,
            subscribers=subscribers,
        )
        summary = self.dispatch_pending_attempts(message_id=message.id)

        if summary.total_attempts != queued_attempts:
            logger.warning(
                "Pending attempt count changed before in-process dispatch for message_id=%s queued=%s dispatched=%s",
                message.id,
                queued_attempts,
                summary.total_attempts,
            )

        return summary

    def _deliver_attempt(self, *, pending_attempt: PendingNotificationAttempt) -> bool:
        """Send one queued notification attempt and persist the result."""

        self.attempt_repository.mark_processing_started(
            attempt_id=pending_attempt.attempt_id,
            processing_started_at=datetime.now(tz=timezone.utc),
        )

        try:
            strategy = self.strategy_factory.get_strategy(pending_attempt.channel_code)
            result = strategy.send(
                subscriber=pending_attempt.subscriber,
                message=pending_attempt.message,
            )
        except Exception as exc:
            failed_at = datetime.now(tz=timezone.utc)
            self.attempt_repository.mark_failed(
                attempt_id=pending_attempt.attempt_id,
                failure_reason=str(exc),
                processed_at=failed_at,
                next_retry_at=self._next_retry_at(
                    pending_attempt=pending_attempt,
                    processed_at=failed_at,
                ),
            )
            logger.exception(
                "Notification delivery failed for attempt_id=%s message_id=%s user_id=%s channel=%s",
                pending_attempt.attempt_id,
                pending_attempt.message.id,
                pending_attempt.subscriber.user_id,
                pending_attempt.channel_code,
            )
            return False

        self.attempt_repository.mark_sent(
            attempt_id=pending_attempt.attempt_id,
            provider_reference=result.provider_reference,
            delivered_at=result.delivered_at,
        )
        logger.info(
            "Notification delivery succeeded for attempt_id=%s message_id=%s user_id=%s channel=%s",
            pending_attempt.attempt_id,
            pending_attempt.message.id,
            pending_attempt.subscriber.user_id,
            pending_attempt.channel_code,
        )
        return True

    @staticmethod
    def _next_retry_at(
        *,
        pending_attempt: PendingNotificationAttempt,
        processed_at: datetime,
    ) -> datetime | None:
        """Return the next retry timestamp for a failed attempt."""

        del pending_attempt, processed_at
        return None
