"""Repository access for inbound messages."""

from __future__ import annotations

from sqlalchemy import select

from app.models import Message
from app.services.types import PersistedMessage

from .base import BaseRepository


class MessageRepository(BaseRepository):
    """Create and load submitted message records."""

    def get_by_idempotency_key(
        self,
        *,
        idempotency_key: str,
    ) -> PersistedMessage | None:
        """Return the message stored for an idempotency key, if one exists."""

        statement = select(
            Message.id,
            Message.category_code,
            Message.body,
            Message.created_at,
            Message.idempotency_key,
        ).where(Message.idempotency_key == idempotency_key)
        row = self.session.execute(statement).tuples().one_or_none()
        if row is None:
            return None

        message_id, category_code, body, created_at, row_idempotency_key = row
        return PersistedMessage(
            id=message_id,
            category_code=category_code,
            body=body,
            created_at=created_at,
            idempotency_key=row_idempotency_key,
        )

    def create(
        self,
        *,
        category_code: str,
        body: str,
        idempotency_key: str | None = None,
    ) -> PersistedMessage:
        """Persist a message and return the normalized repository result."""

        message = Message(
            category_code=category_code,
            body=body,
            idempotency_key=idempotency_key,
        )
        self.session.add(message)
        self.session.flush()
        self.session.refresh(message)
        return self._to_result(message)

    @staticmethod
    def _to_result(message: Message) -> PersistedMessage:
        """Map the ORM entity to a transport-agnostic result."""

        return PersistedMessage(
            id=message.id,
            category_code=message.category_code,
            body=message.body,
            created_at=message.created_at,
            idempotency_key=message.idempotency_key,
        )
