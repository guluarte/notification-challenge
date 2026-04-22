"""Resolve subscribers eligible for a submitted message."""

from __future__ import annotations

import logging

from .types import (
    CategorySubscriptionRepositoryProtocol,
    ChannelPreferenceRepositoryProtocol,
    ResolvedSubscriber,
    UserDirectoryRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class SubscriberResolverService:
    """Service for resolving subscribed users and their channel preferences."""

    def __init__(
        self,
        *,
        user_repository: UserDirectoryRepositoryProtocol,
        subscription_repository: CategorySubscriptionRepositoryProtocol,
        channel_preference_repository: ChannelPreferenceRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository
        self.channel_preference_repository = channel_preference_repository

    def resolve_subscribers(self, *, category_code: str) -> list[ResolvedSubscriber]:
        """Return subscribers eligible for the message category."""

        subscribed_user_ids = self.subscription_repository.list_subscribed_user_ids(
            category_code=category_code
        )
        if len(subscribed_user_ids) == 0:
            logger.info(
                "Resolved 0 eligible subscribers for category=%s", category_code
            )
            return []

        channel_codes_by_user_id = (
            self.channel_preference_repository.list_channel_codes_by_user_ids(
                user_ids=subscribed_user_ids
            )
        )
        user_ids_with_channels = [
            user_id
            for user_id in subscribed_user_ids
            if len(channel_codes_by_user_id.get(user_id, ())) > 0
        ]
        skipped_without_channels = len(subscribed_user_ids) - len(
            user_ids_with_channels
        )
        if len(user_ids_with_channels) == 0:
            logger.info(
                "Resolved 0 eligible subscribers for category=%s (skipped_without_channels=%s)",
                category_code,
                skipped_without_channels,
            )
            return []

        users = self.user_repository.list_by_ids(user_ids=user_ids_with_channels)

        subscribers: list[ResolvedSubscriber] = []
        for user in users:
            channel_codes = channel_codes_by_user_id[user.user_id]

            subscribers.append(
                ResolvedSubscriber(
                    user_id=user.user_id,
                    name=user.name,
                    email=user.email,
                    phone_number=user.phone_number,
                    channel_codes=channel_codes,
                )
            )

        logger.info(
            "Resolved %s eligible subscribers for category=%s (skipped_without_channels=%s)",
            len(subscribers),
            category_code,
            skipped_without_channels,
        )
        return subscribers
