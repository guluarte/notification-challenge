"""Message intake orchestration."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import InfrastructureError, ServiceUnavailableError

from .types import (
    CategoryRepositoryProtocol,
    DispatchSummary,
    MessageCreationResult,
    MessageRepositoryProtocol,
    NotificationDispatcherProtocol,
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
        dispatch_immediately: bool = True,
    ) -> MessageCreationResult:
        """Persist the message and fan it out to subscribed users."""

        if not self.category_repository.exists(category_code):
            raise ServiceUnavailableError(
                "The notification category catalog is unavailable."
            )

        logger.info("Processing inbound message for category=%s", category_code)

        try:
            message = self.message_repository.create(
                category_code=category_code, body=body
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
        )
