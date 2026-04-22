"""Repository access for notification attempt audit rows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.sql.elements import ColumnElement
from app.models import Message, NotificationAttempt
from app.models.enums import DeliveryStatus
from app.services.types import (
    MessageDispatchState,
    NotificationLogEntry,
    NotificationLogFilters,
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

    def claim_pending_attempts(
        self,
        *,
        message_id: int | None = None,
        limit: int | None = None,
    ) -> list[PendingNotificationAttempt]:
        """Claim pending attempts that are eligible for execution."""

        ready_at = datetime.now(tz=timezone.utc)
        statement = (
            select(
                NotificationAttempt.id,
                NotificationAttempt.message_id,
                NotificationAttempt.category_code,
                NotificationAttempt.message_body,
                Message.created_at,
                NotificationAttempt.user_id,
                NotificationAttempt.recipient_snapshot,
                NotificationAttempt.channel_code,
                NotificationAttempt.attempt_number,
            )
            .join(Message, NotificationAttempt.message_id == Message.id)
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
            .with_for_update(of=NotificationAttempt, skip_locked=True)
        )
        if message_id is not None:
            statement = statement.where(NotificationAttempt.message_id == message_id)
        if limit is not None:
            statement = statement.limit(limit)

        return [
            self._to_pending_attempt(
                attempt_id=attempt_id,
                message_id=row_message_id,
                category_code=category_code,
                message_body=message_body,
                message_created_at=message_created_at,
                user_id=user_id,
                recipient_snapshot=recipient_snapshot,
                channel_code=channel_code,
                attempt_number=attempt_number,
            )
            for (
                attempt_id,
                row_message_id,
                category_code,
                message_body,
                message_created_at,
                user_id,
                recipient_snapshot,
                channel_code,
                attempt_number,
            ) in self.session.execute(statement).tuples()
        ]

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

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        filters: NotificationLogFilters,
    ) -> list[NotificationLogEntry]:
        """Return notification attempts sorted from newest to oldest."""

        filter_conditions = self._log_filter_conditions(filters)
        statement = (
            select(
                NotificationAttempt.id,
                NotificationAttempt.message_id,
                NotificationAttempt.category_code,
                NotificationAttempt.message_body,
                NotificationAttempt.user_id,
                NotificationAttempt.recipient_snapshot,
                NotificationAttempt.channel_code,
                NotificationAttempt.status,
                NotificationAttempt.attempt_number,
                NotificationAttempt.attempted_at,
                NotificationAttempt.processing_started_at,
                NotificationAttempt.processed_at,
                NotificationAttempt.delivered_at,
                NotificationAttempt.last_error_at,
                NotificationAttempt.next_retry_at,
                NotificationAttempt.failure_reason,
                NotificationAttempt.provider_reference,
            )
            .where(*filter_conditions)
            .order_by(
                NotificationAttempt.attempted_at.desc(),
                NotificationAttempt.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return [
            self._to_log_entry(
                attempt_id=attempt_id,
                message_id=message_id,
                category_code=category_code,
                message_body=message_body,
                user_id=user_id,
                recipient_snapshot=recipient_snapshot,
                channel_code=channel_code,
                status=status,
                attempt_number=attempt_number,
                attempted_at=attempted_at,
                processing_started_at=processing_started_at,
                processed_at=processed_at,
                delivered_at=delivered_at,
                last_error_at=last_error_at,
                next_retry_at=next_retry_at,
                failure_reason=failure_reason,
                provider_reference=provider_reference,
            )
            for (
                attempt_id,
                message_id,
                category_code,
                message_body,
                user_id,
                recipient_snapshot,
                channel_code,
                status,
                attempt_number,
                attempted_at,
                processing_started_at,
                processed_at,
                delivered_at,
                last_error_at,
                next_retry_at,
                failure_reason,
                provider_reference,
            ) in self.session.execute(statement).tuples()
        ]

    def count_all(self, *, filters: NotificationLogFilters) -> int:
        """Return the total number of notification attempt rows."""

        filter_conditions = self._log_filter_conditions(filters)
        total = self.session.scalar(
            select(func.count(NotificationAttempt.id))
            .select_from(NotificationAttempt)
            .where(*filter_conditions)
        )
        return int(total or 0)

    def summarize_for_message(self, *, message_id: int) -> MessageDispatchState:
        """Return aggregate dispatch state for a message."""

        total_attempts = self.session.scalar(
            select(func.count(NotificationAttempt.id)).where(
                NotificationAttempt.message_id == message_id
            )
        )
        total_users = self.session.scalar(
            select(func.count(func.distinct(NotificationAttempt.user_id))).where(
                NotificationAttempt.message_id == message_id
            )
        )
        sent = self.session.scalar(
            select(func.count(NotificationAttempt.id)).where(
                NotificationAttempt.message_id == message_id,
                NotificationAttempt.status == DeliveryStatus.SENT.value,
            )
        )
        failed = self.session.scalar(
            select(func.count(NotificationAttempt.id)).where(
                NotificationAttempt.message_id == message_id,
                NotificationAttempt.status == DeliveryStatus.FAILED.value,
            )
        )
        return MessageDispatchState(
            total_users=int(total_users or 0),
            total_attempts=int(total_attempts or 0),
            sent=int(sent or 0),
            failed=int(failed or 0),
        )

    @staticmethod
    def _snapshot(subscriber: ResolvedSubscriber) -> dict[str, Any]:
        """Return the recipient snapshot stored with the attempt."""

        return {
            "name": subscriber.name,
            "email": subscriber.email,
            "phone_number": subscriber.phone_number,
        }

    @staticmethod
    def _escape_like_term(term: str) -> str:
        """Escape wildcard characters for user-supplied search terms."""

        return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @classmethod
    def _log_filter_conditions(
        cls,
        filters: NotificationLogFilters,
    ) -> list[ColumnElement[bool]]:
        """Build reusable SQL conditions for log list and count queries."""

        conditions: list[ColumnElement[bool]] = []
        if filters.category_code is not None:
            conditions.append(
                NotificationAttempt.category_code == filters.category_code
            )
        if filters.channel_code is not None:
            conditions.append(NotificationAttempt.channel_code == filters.channel_code)
        if filters.status is not None:
            conditions.append(NotificationAttempt.status == filters.status.value)
        if filters.message_id is not None:
            conditions.append(NotificationAttempt.message_id == filters.message_id)
        if filters.user_id is not None:
            conditions.append(NotificationAttempt.user_id == filters.user_id)
        if filters.search is not None:
            search_pattern = f"%{cls._escape_like_term(filters.search)}%"
            conditions.append(
                or_(
                    NotificationAttempt.message_body.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    NotificationAttempt.failure_reason.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    NotificationAttempt.provider_reference.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    NotificationAttempt.recipient_snapshot["name"].astext.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    NotificationAttempt.recipient_snapshot["email"].astext.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                    NotificationAttempt.recipient_snapshot["phone_number"].astext.ilike(
                        search_pattern,
                        escape="\\",
                    ),
                )
            )
        return conditions

    @staticmethod
    def _to_pending_attempt(
        *,
        attempt_id: int,
        message_id: int,
        category_code: str,
        message_body: str,
        message_created_at: datetime,
        user_id: int,
        recipient_snapshot: dict[str, Any],
        channel_code: str,
        attempt_number: int,
    ) -> PendingNotificationAttempt:
        """Map projected attempt columns to the pending dispatch structure."""

        return PendingNotificationAttempt(
            attempt_id=attempt_id,
            message=PersistedMessage(
                id=message_id,
                category_code=category_code,
                body=message_body,
                created_at=message_created_at,
            ),
            subscriber=ResolvedSubscriber(
                user_id=user_id,
                name=str(recipient_snapshot.get("name", "")),
                email=str(recipient_snapshot.get("email", "")),
                phone_number=str(recipient_snapshot.get("phone_number", "")),
                channel_codes=(channel_code,),
            ),
            channel_code=channel_code,
            attempt_number=attempt_number,
        )

    @staticmethod
    def _to_log_entry(
        *,
        attempt_id: int,
        message_id: int,
        category_code: str,
        message_body: str,
        user_id: int,
        recipient_snapshot: dict[str, Any],
        channel_code: str,
        status: str,
        attempt_number: int,
        attempted_at: datetime,
        processing_started_at: datetime | None,
        processed_at: datetime | None,
        delivered_at: datetime | None,
        last_error_at: datetime | None,
        next_retry_at: datetime | None,
        failure_reason: str | None,
        provider_reference: str | None,
    ) -> NotificationLogEntry:
        """Map projected attempt columns to the service log structure."""

        return NotificationLogEntry(
            attempt_id=attempt_id,
            message_id=message_id,
            category_code=category_code,
            body=message_body,
            user_id=user_id,
            user_name=str(recipient_snapshot.get("name", "")),
            user_email=str(recipient_snapshot.get("email", "")),
            user_phone_number=str(recipient_snapshot.get("phone_number", "")),
            channel_code=channel_code,
            status=DeliveryStatus(status),
            attempt_number=attempt_number,
            attempted_at=attempted_at,
            processing_started_at=processing_started_at,
            processed_at=processed_at,
            delivered_at=delivered_at,
            last_error_at=last_error_at,
            next_retry_at=next_retry_at,
            failure_reason=failure_reason,
            provider_reference=provider_reference,
        )
