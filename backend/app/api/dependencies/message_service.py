"""FastAPI dependency for composing the message intake service."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.repositories.categories import NotificationCategoryRepository
from app.repositories.messages import MessageRepository
from app.repositories.notification_deliveries import NotificationAttemptRepository
from app.repositories.user_category_subscriptions import (
    UserCategorySubscriptionRepository,
)
from app.repositories.user_channel_preferences import UserChannelPreferenceRepository
from app.repositories.users import UserRepository
from app.services.message_service import MessageService
from app.services.notification_dispatcher import NotificationDispatcherService
from app.services.subscriber_resolver import SubscriberResolverService

from .db import DBSessionDep
from .notification_strategy_factory import get_notification_strategy_factory


def get_message_service(db_session: DBSessionDep) -> MessageService:
    """Compose the message intake service for the current request."""

    user_repository = UserRepository(db_session)
    subscription_repository = UserCategorySubscriptionRepository(db_session)
    channel_preference_repository = UserChannelPreferenceRepository(db_session)
    attempt_repository = NotificationAttemptRepository(db_session)
    subscriber_resolver = SubscriberResolverService(
        user_repository=user_repository,
        subscription_repository=subscription_repository,
        channel_preference_repository=channel_preference_repository,
    )
    dispatcher = NotificationDispatcherService(
        attempt_repository=attempt_repository,
        strategy_factory=get_notification_strategy_factory(),
    )
    return MessageService(
        session=db_session,
        category_repository=NotificationCategoryRepository(db_session),
        message_repository=MessageRepository(db_session),
        subscriber_resolver=subscriber_resolver,
        notification_dispatcher=dispatcher,
    )


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
