"""Tests for subscriber resolution behavior."""

from __future__ import annotations

from collections.abc import Sequence

from app.services.subscriber_resolver import SubscriberResolverService
from app.services.types import ResolvedSubscriber, UserProfile


class FakeUserRepository:
    """User repository double for subscriber resolution tests."""

    def __init__(self, users: list[UserProfile]) -> None:
        self.users = users
        self.requested_user_ids: list[int] = []

    def list_by_ids(self, *, user_ids: Sequence[int]) -> list[UserProfile]:
        self.requested_user_ids = list(user_ids)
        return self.users


class FakeSubscriptionRepository:
    """Subscription repository double for subscriber resolution tests."""

    def __init__(self, user_ids: list[int]) -> None:
        self.user_ids = user_ids
        self.requested_category_code: str | None = None

    def list_subscribed_user_ids(self, *, category_code: str) -> list[int]:
        self.requested_category_code = category_code
        return self.user_ids


class FakeChannelPreferenceRepository:
    """Channel preference repository double for subscriber resolution tests."""

    def __init__(self, channel_codes_by_user_id: dict[int, tuple[str, ...]]) -> None:
        self.channel_codes_by_user_id = channel_codes_by_user_id
        self.requested_user_ids: list[int] = []

    def list_channel_codes_by_user_ids(
        self,
        *,
        user_ids: Sequence[int],
    ) -> dict[int, tuple[str, ...]]:
        self.requested_user_ids = list(user_ids)
        return self.channel_codes_by_user_id


def test_subscriber_resolver_composes_user_and_channel_data() -> None:
    """The resolver should assemble subscriber records from repository data."""

    user_repository = FakeUserRepository(
        users=[
            UserProfile(
                user_id=1,
                name="Alex",
                email="alex@example.com",
                phone_number="+15550000001",
            )
        ]
    )
    subscription_repository = FakeSubscriptionRepository(user_ids=[1])
    channel_preference_repository = FakeChannelPreferenceRepository(
        channel_codes_by_user_id={1: ("email", "push")}
    )
    service = SubscriberResolverService(
        user_repository=user_repository,
        subscription_repository=subscription_repository,
        channel_preference_repository=channel_preference_repository,
    )

    result = service.resolve_subscribers(category_code="sports")

    assert result == [
        ResolvedSubscriber(
            user_id=1,
            name="Alex",
            email="alex@example.com",
            phone_number="+15550000001",
            channel_codes=("email", "push"),
        )
    ]
    assert subscription_repository.requested_category_code == "sports"
    assert user_repository.requested_user_ids == [1]
    assert channel_preference_repository.requested_user_ids == [1]


def test_subscriber_resolver_filters_out_subscribers_without_channels() -> None:
    """Users without configured channels should not be considered eligible."""

    user_repository = FakeUserRepository(
        users=[
            UserProfile(
                user_id=1,
                name="Alex",
                email="alex@example.com",
                phone_number="+15550000001",
            ),
            UserProfile(
                user_id=2,
                name="Jordan",
                email="jordan@example.com",
                phone_number="+15550000002",
            ),
        ]
    )
    subscription_repository = FakeSubscriptionRepository(user_ids=[1, 2])
    channel_preference_repository = FakeChannelPreferenceRepository(
        channel_codes_by_user_id={1: ("email",)}
    )
    service = SubscriberResolverService(
        user_repository=user_repository,
        subscription_repository=subscription_repository,
        channel_preference_repository=channel_preference_repository,
    )

    result = service.resolve_subscribers(category_code="sports")

    assert result == [
        ResolvedSubscriber(
            user_id=1,
            name="Alex",
            email="alex@example.com",
            phone_number="+15550000001",
            channel_codes=("email",),
        )
    ]
    assert subscription_repository.requested_category_code == "sports"
    assert user_repository.requested_user_ids == [1, 2]
    assert channel_preference_repository.requested_user_ids == [1, 2]


def test_subscriber_resolver_short_circuits_when_no_users_are_subscribed() -> None:
    """No directory or preference lookups should run without subscriptions."""

    user_repository = FakeUserRepository(users=[])
    subscription_repository = FakeSubscriptionRepository(user_ids=[])
    channel_preference_repository = FakeChannelPreferenceRepository(
        channel_codes_by_user_id={}
    )
    service = SubscriberResolverService(
        user_repository=user_repository,
        subscription_repository=subscription_repository,
        channel_preference_repository=channel_preference_repository,
    )

    result = service.resolve_subscribers(category_code="movies")

    assert result == []
    assert subscription_repository.requested_category_code == "movies"
    assert user_repository.requested_user_ids == []
    assert channel_preference_repository.requested_user_ids == []
