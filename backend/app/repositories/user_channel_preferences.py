"""Repository access for user channel preferences."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models import UserChannelPreference

from .base import BaseRepository


class UserChannelPreferenceRepository(BaseRepository):
    """Query helpers for user notification channel preferences."""

    def list_channel_codes_by_user_ids(
        self,
        *,
        user_ids: Sequence[int],
    ) -> dict[int, tuple[str, ...]]:
        """Return preferred channel codes keyed by user identifier."""

        if len(user_ids) == 0:
            return {}

        statement = (
            select(UserChannelPreference)
            .where(UserChannelPreference.user_id.in_(user_ids))
            .order_by(
                UserChannelPreference.user_id.asc(),
                UserChannelPreference.channel_code.asc(),
            )
        )
        channel_codes_by_user_id: dict[int, list[str]] = {}
        preferences = self.session.scalars(statement).all()
        for preference in preferences:
            channel_codes_by_user_id.setdefault(preference.user_id, []).append(
                preference.channel_code
            )

        return {
            user_id: tuple(channel_codes)
            for user_id, channel_codes in channel_codes_by_user_id.items()
        }
