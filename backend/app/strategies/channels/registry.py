"""Registry for notification channel strategies."""

from __future__ import annotations

from collections.abc import Iterable

from app.core.exceptions import StrategyConfigurationError

from .base import NotificationStrategy


class NotificationStrategyFactory:
    """Resolve channel strategies by stable channel code."""

    def __init__(self, strategies: Iterable[NotificationStrategy]) -> None:
        self._strategies = {strategy.channel_code: strategy for strategy in strategies}

    def get_strategy(self, channel_code: str) -> NotificationStrategy:
        """Return the configured strategy for a channel code."""

        strategy = self._strategies.get(channel_code)
        if strategy is None:
            raise StrategyConfigurationError(
                f"No notification strategy is configured for channel '{channel_code}'."
            )
        return strategy
