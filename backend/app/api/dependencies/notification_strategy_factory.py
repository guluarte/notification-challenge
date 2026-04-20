"""Shared dependency helpers for notification channel strategies."""

from __future__ import annotations

from app.strategies.channels.email import EmailNotificationStrategy
from app.strategies.channels.push import PushNotificationStrategy
from app.strategies.channels.registry import NotificationStrategyFactory
from app.strategies.channels.sms import SmsNotificationStrategy

_strategy_factory = NotificationStrategyFactory(
    strategies=(
        EmailNotificationStrategy(),
        SmsNotificationStrategy(),
        PushNotificationStrategy(),
    )
)


def get_notification_strategy_factory() -> NotificationStrategyFactory:
    """Return the shared strategy factory for channel dispatch."""

    return _strategy_factory
