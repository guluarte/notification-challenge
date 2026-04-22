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

        message = self.session.scalars(
            select(Message).where(Message.idempotency_key == idempotency_key)
        ).one_or_none()
        if message is None:
            return None
        return self._to_result(message)

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
