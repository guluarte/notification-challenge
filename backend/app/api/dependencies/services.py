"""FastAPI dependencies that compose repositories and services."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.repositories.categories import NotificationCategoryRepository
from app.repositories.messages import MessageRepository
from app.repositories.notification_deliveries import NotificationDeliveryRepository
from app.repositories.users import UserRepository
from app.services.message_service import MessageService
from app.services.notification_dispatcher import NotificationDispatcherService
from app.services.notification_log_service import NotificationLogService
from app.services.subscriber_resolver import SubscriberResolverService
from app.strategies.channels.email import EmailNotificationStrategy
from app.strategies.channels.push import PushNotificationStrategy
from app.strategies.channels.registry import NotificationStrategyFactory
from app.strategies.channels.sms import SmsNotificationStrategy

from .db import DBSessionDep

_strategy_factory = NotificationStrategyFactory(
    strategies=(
        EmailNotificationStrategy(),
        SmsNotificationStrategy(),
        PushNotificationStrategy(),
    )
)


def get_message_service(db_session: DBSessionDep) -> MessageService:
    """Compose the message intake service for the current request."""

    user_repository = UserRepository(db_session)
    delivery_repository = NotificationDeliveryRepository(db_session)
    subscriber_resolver = SubscriberResolverService(user_repository=user_repository)
    dispatcher = NotificationDispatcherService(
        delivery_repository=delivery_repository,
        strategy_factory=_strategy_factory,
    )
    return MessageService(
        session=db_session,
        category_repository=NotificationCategoryRepository(db_session),
        message_repository=MessageRepository(db_session),
        subscriber_resolver=subscriber_resolver,
        notification_dispatcher=dispatcher,
    )


def get_notification_log_service(db_session: DBSessionDep) -> NotificationLogService:
    """Compose the log listing service for the current request."""

    return NotificationLogService(
        delivery_repository=NotificationDeliveryRepository(db_session)
    )


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
NotificationLogServiceDep = Annotated[
    NotificationLogService, Depends(get_notification_log_service)
]
