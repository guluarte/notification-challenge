"""Tests for concrete notification strategies and the strategy registry."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.exceptions import StrategyConfigurationError
from app.services.types import DeliveryResult, PersistedMessage, ResolvedSubscriber
from app.strategies.channels.base import NotificationStrategy
from app.strategies.channels.email import EmailNotificationStrategy
from app.strategies.channels.push import PushNotificationStrategy
from app.strategies.channels.registry import NotificationStrategyFactory
from app.strategies.channels.sms import SmsNotificationStrategy


class DuplicateEmailStrategy(NotificationStrategy):
    """Test double used to validate duplicate strategy registration."""

    channel_code = "email"

    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        del subscriber, message
        raise AssertionError("The duplicate strategy should never be invoked.")


def build_message() -> PersistedMessage:
    """Return a stable persisted message fixture."""

    return PersistedMessage(
        id=17,
        category_code="sports",
        body="Final score update",
        created_at=datetime(2026, 4, 19, tzinfo=timezone.utc),
    )


def build_subscriber() -> ResolvedSubscriber:
    """Return a stable subscriber fixture."""

    return ResolvedSubscriber(
        user_id=8,
        name="Taylor",
        email="taylor@example.com",
        phone_number="+15550000008",
        channel_codes=("email", "sms", "push"),
    )


@pytest.mark.parametrize(
    ("strategy", "expected_provider_reference"),
    [
        (EmailNotificationStrategy(), "email-17-8"),
        (SmsNotificationStrategy(), "sms-17-8"),
        (PushNotificationStrategy(), "push-17-8"),
    ],
)
def test_notification_strategy_returns_channel_specific_delivery_result(
    strategy: NotificationStrategy,
    expected_provider_reference: str,
) -> None:
    """Each concrete strategy should return a success result for its channel."""

    result = strategy.send(
        subscriber=build_subscriber(),
        message=build_message(),
    )

    assert result.provider_reference == expected_provider_reference
    assert result.delivered_at.tzinfo == timezone.utc


def test_notification_strategy_factory_returns_configured_strategy() -> None:
    """The factory should resolve the configured strategy instance by channel."""

    email_strategy = EmailNotificationStrategy()
    factory = NotificationStrategyFactory(
        strategies=(
            email_strategy,
            SmsNotificationStrategy(),
            PushNotificationStrategy(),
        )
    )

    resolved_strategy = factory.get_strategy("email")

    assert resolved_strategy is email_strategy


def test_notification_strategy_factory_raises_for_missing_channel() -> None:
    """Resolving an unconfigured channel should raise a configuration error."""

    factory = NotificationStrategyFactory(strategies=(EmailNotificationStrategy(),))

    with pytest.raises(StrategyConfigurationError) as exc_info:
        factory.get_strategy("push")

    assert (
        exc_info.value.detail
        == "No notification strategy is configured for channel 'push'."
    )


def test_notification_strategy_factory_rejects_duplicate_channel_codes() -> None:
    """Duplicate registrations should fail fast during application wiring."""

    with pytest.raises(StrategyConfigurationError) as exc_info:
        NotificationStrategyFactory(
            strategies=(EmailNotificationStrategy(), DuplicateEmailStrategy())
        )

    assert (
        exc_info.value.detail
        == "Duplicate notification strategy configured for channel 'email'."
    )
