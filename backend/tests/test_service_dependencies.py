"""Tests for FastAPI service dependency composition."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.dependencies.services import (
    get_message_service,
    get_notification_log_service,
)
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
from app.services.notification_log_service import NotificationLogService
from app.services.subscriber_resolver import SubscriberResolverService
from app.strategies.channels.email import EmailNotificationStrategy
from app.strategies.channels.push import PushNotificationStrategy
from app.strategies.channels.sms import SmsNotificationStrategy


def test_get_message_service_composes_default_repositories_and_strategies() -> None:
    """The dependency should wire the concrete repositories and strategies."""

    session = Session()

    service = get_message_service(session)

    assert isinstance(service, MessageService)
    assert service.session is session
    assert isinstance(service.category_repository, NotificationCategoryRepository)
    assert service.category_repository.session is session
    assert isinstance(service.message_repository, MessageRepository)
    assert service.message_repository.session is session
    assert isinstance(service.subscriber_resolver, SubscriberResolverService)
    assert isinstance(service.subscriber_resolver.user_repository, UserRepository)
    assert service.subscriber_resolver.user_repository.session is session
    assert isinstance(
        service.subscriber_resolver.subscription_repository,
        UserCategorySubscriptionRepository,
    )
    assert service.subscriber_resolver.subscription_repository.session is session
    assert isinstance(
        service.subscriber_resolver.channel_preference_repository,
        UserChannelPreferenceRepository,
    )
    assert service.subscriber_resolver.channel_preference_repository.session is session
    assert isinstance(service.notification_dispatcher, NotificationDispatcherService)
    assert isinstance(
        service.notification_dispatcher.attempt_repository,
        NotificationAttemptRepository,
    )
    assert service.notification_dispatcher.attempt_repository.session is session
    assert isinstance(
        service.notification_dispatcher.strategy_factory.get_strategy("email"),
        EmailNotificationStrategy,
    )
    assert isinstance(
        service.notification_dispatcher.strategy_factory.get_strategy("sms"),
        SmsNotificationStrategy,
    )
    assert isinstance(
        service.notification_dispatcher.strategy_factory.get_strategy("push"),
        PushNotificationStrategy,
    )

    session.close()


def test_get_notification_log_service_uses_attempt_repository() -> None:
    """The log dependency should compose the log service with the attempt repo."""

    session = Session()

    service = get_notification_log_service(session)

    assert isinstance(service, NotificationLogService)
    assert isinstance(service.attempt_repository, NotificationAttemptRepository)
    assert service.attempt_repository.session is session

    session.close()
