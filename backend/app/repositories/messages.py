"""Repository access for inbound messages."""

from __future__ import annotations

from app.models import Message
from app.services.types import PersistedMessage

from .base import BaseRepository


class MessageRepository(BaseRepository):
    """Create and load submitted message records."""

    def create(self, *, category_code: str, body: str) -> PersistedMessage:
        """Persist a message and return the normalized repository result."""

        message = Message(category_code=category_code, body=body)
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
        )
