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
            select(
                UserChannelPreference.user_id,
                UserChannelPreference.channel_code,
            )
            .where(UserChannelPreference.user_id.in_(user_ids))
            .order_by(
                UserChannelPreference.user_id.asc(),
                UserChannelPreference.channel_code.asc(),
            )
        )
        channel_codes_by_user_id: dict[int, list[str]] = {}
        for user_id, channel_code in self.session.execute(statement).tuples():
            channel_codes_by_user_id.setdefault(user_id, []).append(channel_code)

        return {
            user_id: tuple(channel_codes)
            for user_id, channel_codes in channel_codes_by_user_id.items()
        }
