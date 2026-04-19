"""Notification channel strategy contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.types import DeliveryResult, PersistedMessage, ResolvedSubscriber


class NotificationStrategy(ABC):
    """Interface implemented by each outbound notification channel."""

    channel_code: str

    @abstractmethod
    def send(
        self,
        *,
        subscriber: ResolvedSubscriber,
        message: PersistedMessage,
    ) -> DeliveryResult:
        """Send the message to the subscriber through this channel."""
