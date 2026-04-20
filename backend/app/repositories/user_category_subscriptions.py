"""Repository access for user category subscriptions."""

from __future__ import annotations

from sqlalchemy import select

from app.models import UserCategorySubscription

from .base import BaseRepository


class UserCategorySubscriptionRepository(BaseRepository):
    """Query helpers for category-based user subscription lookups."""

    def list_subscribed_user_ids(self, *, category_code: str) -> list[int]:
        """Return subscribed user identifiers ordered by user id."""

        statement = (
            select(UserCategorySubscription.user_id)
            .where(UserCategorySubscription.category_code == category_code)
            .order_by(UserCategorySubscription.user_id.asc())
        )
        return list(self.session.scalars(statement))
