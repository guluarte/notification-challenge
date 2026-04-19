"""Tests for subscriber resolution behavior."""

from __future__ import annotations

from app.services.subscriber_resolver import SubscriberResolverService
from app.services.types import ResolvedSubscriber


class FakeUserRepository:
    """User repository double for subscriber resolution tests."""

    def __init__(self, subscribers: list[ResolvedSubscriber]) -> None:
        self.subscribers = subscribers
        self.requested_category_code: str | None = None

    def list_subscribed_users(self, *, category_code: str) -> list[ResolvedSubscriber]:
        self.requested_category_code = category_code
        return self.subscribers


def test_subscriber_resolver_returns_repository_results() -> None:
    """The resolver should delegate category lookups to the repository."""

    subscribers = [
        ResolvedSubscriber(
            user_id=1,
            name="Alex",
            email="alex@example.com",
            phone_number="+15550000001",
            channel_codes=("email", "push"),
        )
    ]
    repository = FakeUserRepository(subscribers=subscribers)
    service = SubscriberResolverService(user_repository=repository)

    result = service.resolve_subscribers(category_code="sports")

    assert result == subscribers
    assert repository.requested_category_code == "sports"
