"""Tests for recipient-oriented repository classes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.base import Base
from app.repositories.user_category_subscriptions import (
    UserCategorySubscriptionRepository,
)
from app.repositories.user_channel_preferences import UserChannelPreferenceRepository
from app.repositories.users import UserRepository
from app.seeders import seed_database
from app.services.types import UserProfile


@contextmanager
def _session_scope() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            table
            for table in Base.metadata.sorted_tables
            if table.name
            in {
                "notification_categories",
                "notification_channels",
                "users",
                "user_category_subscriptions",
                "user_channel_preferences",
            }
        ],
    )

    with Session(engine) as session:
        seed_database(session)
        session.commit()
        yield session

    engine.dispose()


def test_user_repository_lists_directory_records_by_id() -> None:
    """The user repository should return user directory rows ordered by id."""

    with _session_scope() as session:
        repository = UserRepository(session)

        users = repository.list_by_ids(user_ids=[4, 1, 3])

    assert users == [
        UserProfile(
            user_id=1,
            name="Alex Morgan",
            email="alex.morgan@example.com",
            phone_number="+15550001001",
        ),
        UserProfile(
            user_id=3,
            name="Sam Rivera",
            email="sam.rivera@example.com",
            phone_number="+15550001003",
        ),
        UserProfile(
            user_id=4,
            name="Casey Patel",
            email="casey.patel@example.com",
            phone_number="+15550001004",
        ),
    ]


def test_subscription_repository_lists_user_ids_for_category() -> None:
    """The subscription repository should return subscribed user ids in order."""

    with _session_scope() as session:
        repository = UserCategorySubscriptionRepository(session)

        user_ids = repository.list_subscribed_user_ids(category_code="finance")

    assert user_ids == [1, 3, 4]


def test_channel_preference_repository_groups_channels_by_user() -> None:
    """The channel preference repository should return sorted channels per user."""

    with _session_scope() as session:
        repository = UserChannelPreferenceRepository(session)

        channel_codes_by_user_id = repository.list_channel_codes_by_user_ids(
            user_ids=[1, 2, 3]
        )

    assert channel_codes_by_user_id == {
        1: ("email", "push"),
        2: ("sms",),
        3: ("email", "push", "sms"),
    }
