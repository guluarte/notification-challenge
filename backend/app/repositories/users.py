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

        statement = select(User).where(User.id.in_(user_ids)).order_by(User.id.asc())
        users = self.session.scalars(statement).all()
        return [self._to_user_profile(user) for user in users]

    @staticmethod
    def _to_user_profile(user: User) -> UserProfile:
        """Map an ORM user to the service layer directory structure."""

        return UserProfile(
            user_id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
        )
