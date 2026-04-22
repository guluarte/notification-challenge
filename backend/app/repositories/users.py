"""Repository access for notification recipients."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models import User
from app.services.types import UserProfile

from .base import BaseRepository


class UserRepository(BaseRepository):
    """Query core user directory records."""

    def list_by_ids(self, *, user_ids: Sequence[int]) -> list[UserProfile]:
        """Return user directory records ordered by identifier."""

        if len(user_ids) == 0:
            return []

        statement = (
            select(User.id, User.name, User.email, User.phone_number)
            .where(User.id.in_(user_ids))
            .order_by(User.id.asc())
        )
        return [
            UserProfile(
                user_id=user_id,
                name=name,
                email=email,
                phone_number=phone_number,
            )
            for user_id, name, email, phone_number in self.session.execute(
                statement
            ).tuples()
        ]
