"""Message intake orchestration."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    IdempotencyConflictError,
    InfrastructureError,
    ServiceUnavailableError,
)

from .types import (
    CategoryRepositoryProtocol,
    DispatchSummary,
    MessageDispatchState,
    MessageCreationResult,
    MessageRepositoryProtocol,
    NotificationDispatcherProtocol,
    PersistedMessage,
    SessionProtocol,
    SubscriberResolverProtocol,
)

logger = logging.getLogger(__name__)


class MessageService:
    """Create a message, resolve subscribers, and dispatch notifications."""

    def __init__(
        self,
        *,
        session: SessionProtocol,
        category_repository: CategoryRepositoryProtocol,
        message_repository: MessageRepositoryProtocol,
        subscriber_resolver: SubscriberResolverProtocol,
        notification_dispatcher: NotificationDispatcherProtocol,
    ) -> None:
        self.session = session
        self.category_repository = category_repository
        self.message_repository = message_repository
        self.subscriber_resolver = subscriber_resolver
        self.notification_dispatcher = notification_dispatcher

    def create_message(
        self,
        *,
        category_code: str,
        body: str,
        idempotency_key: str | None = None,
        dispatch_immediately: bool = True,
    ) -> MessageCreationResult:
        """Persist the message and fan it out to subscribed users."""

        normalized_idempotency_key = self._normalize_idempotency_key(idempotency_key)

        try:
            if not self.category_repository.exists(category_code):
                raise ServiceUnavailableError(
                    "The notification category catalog is unavailable."
                )

            if normalized_idempotency_key is not None:
                existing_message = self.message_repository.get_by_idempotency_key(
                    idempotency_key=normalized_idempotency_key
                )
                if existing_message is not None:
                    return self._replay_existing_message(
                        existing_message=existing_message,
                        category_code=category_code,
                        body=body,
                    )

            logger.info(
                "Processing inbound message for category=%s idempotency_key_present=%s",
                category_code,
                normalized_idempotency_key is not None,
            )
            message = self.message_repository.create(
                category_code=category_code,
                body=body,
                idempotency_key=normalized_idempotency_key,
            )
            subscribers = self.subscriber_resolver.resolve_subscribers(
                category_code=category_code
            )
            queued_attempts = self.notification_dispatcher.prepare_dispatch(
                message=message,
                subscribers=subscribers,
            )
            dispatch_summary = DispatchSummary(
                total_attempts=queued_attempts,
                sent=0,
                failed=0,
            )
            if dispatch_immediately:
                dispatch_summary = (
                    self.notification_dispatcher.dispatch_pending_attempts(
                        message_id=message.id
                    )
                )
            self.session.commit()
        except (ServiceUnavailableError, IdempotencyConflictError):
            raise
        except IntegrityError as exc:
            replayed_result = self._replay_after_idempotency_insert_conflict(
                idempotency_key=normalized_idempotency_key,
                category_code=category_code,
                body=body,
            )
            if replayed_result is not None:
                return replayed_result

            logger.exception(
                "Failed to persist message dispatch state for category=%s",
                category_code,
            )
            raise InfrastructureError("The message could not be persisted.") from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.exception(
                "Failed to persist message dispatch state for category=%s",
                category_code,
            )
            raise InfrastructureError("The message could not be persisted.") from exc

        logger.info(
            (
                "Completed message_id=%s subscribers=%s attempts=%s sent=%s "
                "failed=%s dispatch_immediately=%s"
            ),
            message.id,
            len(subscribers),
            dispatch_summary.total_attempts,
            dispatch_summary.sent,
            dispatch_summary.failed,
            dispatch_immediately,
        )
        return MessageCreationResult(
            message_id=message.id,
            category_code=message.category_code,
            body=message.body,
            total_users=len(subscribers),
            total_attempts=dispatch_summary.total_attempts,
            sent=dispatch_summary.sent,
            failed=dispatch_summary.failed,
            created_at=message.created_at,
            idempotency_key=message.idempotency_key,
        )

    @staticmethod
    def _normalize_idempotency_key(idempotency_key: str | None) -> str | None:
        """Normalize optional idempotency keys from transport inputs."""

        if idempotency_key is None:
            return None

        normalized = idempotency_key.strip()
        if normalized == "":
            return None
        return normalized

    def _replay_after_idempotency_insert_conflict(
        self,
        *,
        idempotency_key: str | None,
        category_code: str,
        body: str,
    ) -> MessageCreationResult | None:
        """Replay an existing message after a concurrent key insert wins."""

        self.session.rollback()

        if idempotency_key is None:
            return None

        logger.warning(
            "Reloading message after idempotency key insert conflict for category=%s",
            category_code,
        )
        try:
            existing_message = self.message_repository.get_by_idempotency_key(
                idempotency_key=idempotency_key
            )
            if existing_message is None:
                logger.warning(
                    "No message found after idempotency key insert conflict for category=%s",
                    category_code,
                )
                return None

            return self._replay_existing_message(
                existing_message=existing_message,
                category_code=category_code,
                body=body,
            )
        except IdempotencyConflictError:
            raise
        except SQLAlchemyError:
            logger.exception(
                "Failed to reload message after idempotency key insert conflict"
            )
            return None

    def _replay_existing_message(
        self,
        *,
        existing_message: PersistedMessage,
        category_code: str,
        body: str,
    ) -> MessageCreationResult:
        """Return the original result for an idempotent duplicate submission."""

        if (
            existing_message.category_code != category_code
            or existing_message.body != body
        ):
            logger.warning(
                "Rejected idempotency key reuse for message_id=%s category=%s",
                existing_message.id,
                category_code,
            )
            raise IdempotencyConflictError(
                "The idempotency key has already been used for a different message."
            )

        dispatch_state = self.notification_dispatcher.summarize_message_dispatch(
            message_id=existing_message.id
        )
        logger.info(
            "Replaying idempotent message result for message_id=%s attempts=%s",
            existing_message.id,
            dispatch_state.total_attempts,
        )
        return self._build_replayed_result(
            message=existing_message,
            dispatch_state=dispatch_state,
        )

    @staticmethod
    def _build_replayed_result(
        *,
        message: PersistedMessage,
        dispatch_state: MessageDispatchState,
    ) -> MessageCreationResult:
        """Build the service result for an already-processed idempotency key."""

        return MessageCreationResult(
            message_id=message.id,
            category_code=message.category_code,
            body=message.body,
            total_users=dispatch_state.total_users,
            total_attempts=dispatch_state.total_attempts,
            sent=dispatch_state.sent,
            failed=dispatch_state.failed,
            created_at=message.created_at,
            idempotency_key=message.idempotency_key,
            was_duplicate=True,
        )
