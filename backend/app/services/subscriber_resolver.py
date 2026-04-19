"""Resolve subscribers eligible for a submitted message."""

from __future__ import annotations

import logging

from .types import ResolvedSubscriber, SubscriberRepositoryProtocol

logger = logging.getLogger(__name__)


class SubscriberResolverService:
    """Service for resolving subscribed users and their channel preferences."""

    def __init__(self, user_repository: SubscriberRepositoryProtocol) -> None:
        self.user_repository = user_repository

    def resolve_subscribers(self, *, category_code: str) -> list[ResolvedSubscriber]:
        """Return subscribers eligible for the message category."""

        subscribers = self.user_repository.list_subscribed_users(
            category_code=category_code
        )
        logger.info(
            "Resolved %s subscribers for category=%s",
            len(subscribers),
            category_code,
        )
        return subscribers
