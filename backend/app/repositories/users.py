"""Repository access for notification recipients."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import User, UserCategorySubscription
from app.services.types import ResolvedSubscriber

from .base import BaseRepository


class UserRepository(BaseRepository):
    """Resolve notification recipients from subscriptions and preferences."""

    def list_subscribed_users(self, *, category_code: str) -> list[ResolvedSubscriber]:
        """Return users subscribed to the category with their channel codes."""

        statement = (
            select(User)
            .join(UserCategorySubscription)
            .options(selectinload(User.channel_preferences))
            .where(UserCategorySubscription.category_code == category_code)
            .order_by(User.id.asc())
        )
        users = self.session.scalars(statement).all()
        return [self._to_resolved_subscriber(user) for user in users]

    @staticmethod
    def _to_resolved_subscriber(user: User) -> ResolvedSubscriber:
        """Map an ORM user to the service layer subscriber structure."""

        channel_codes = tuple(
            sorted(preference.channel_code for preference in user.channel_preferences)
        )
        return ResolvedSubscriber(
            user_id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            channel_codes=channel_codes,
        )
