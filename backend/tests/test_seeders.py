"""Tests for deterministic demo database seeding."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.category import NotificationCategory
from app.models.channel import NotificationChannel
from app.models.user import User
from app.models.user_category_subscription import UserCategorySubscription
from app.models.user_channel_preference import UserChannelPreference
from app.seeders import SeedSummary, seed_database


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
        yield session
    engine.dispose()


def test_seed_database_populates_catalogs_users_and_preferences() -> None:
    with _session_scope() as session:
        summary = seed_database(session)
        session.commit()

        assert summary == SeedSummary(
            categories=3,
            channels=3,
            users=4,
            category_subscriptions=8,
            channel_preferences=7,
        )
        assert tuple(
            session.scalars(
                select(NotificationCategory.code).order_by(NotificationCategory.code)
            )
        ) == ("finance", "movies", "sports")
        assert tuple(
            session.scalars(
                select(NotificationChannel.code).order_by(NotificationChannel.code)
            )
        ) == ("email", "push", "sms")

        users = session.scalars(select(User).order_by(User.id)).all()
        assert [(user.id, user.email) for user in users] == [
            (1, "alex.morgan@example.com"),
            (2, "jordan.lee@example.com"),
            (3, "sam.rivera@example.com"),
            (4, "casey.patel@example.com"),
        ]

        alex_categories = tuple(
            session.scalars(
                select(UserCategorySubscription.category_code)
                .where(UserCategorySubscription.user_id == 1)
                .order_by(UserCategorySubscription.category_code)
            )
        )
        jordan_channels = tuple(
            session.scalars(
                select(UserChannelPreference.channel_code)
                .where(UserChannelPreference.user_id == 2)
                .order_by(UserChannelPreference.channel_code)
            )
        )
        sam_channels = tuple(
            session.scalars(
                select(UserChannelPreference.channel_code)
                .where(UserChannelPreference.user_id == 3)
                .order_by(UserChannelPreference.channel_code)
            )
        )

        assert alex_categories == ("finance", "sports")
        assert jordan_channels == ("sms",)
        assert sam_channels == ("email", "push", "sms")


def test_seed_database_restores_seeded_rows_on_repeat_runs() -> None:
    with _session_scope() as session:
        first_summary = seed_database(session)
        session.commit()

        alex = session.get(User, 1)
        assert alex is not None
        alex.name = "Mutated Name"
        session.execute(
            delete(UserCategorySubscription).where(
                UserCategorySubscription.user_id == 1
            )
        )
        session.execute(
            delete(UserChannelPreference).where(UserChannelPreference.user_id == 2)
        )
        session.add(UserCategorySubscription(user_id=1, category_code="movies"))
        session.add(UserChannelPreference(user_id=2, channel_code="push"))
        session.commit()

        second_summary = seed_database(session)
        session.commit()

        assert first_summary == second_summary
        restored_alex = session.get(User, 1)
        assert restored_alex is not None
        assert restored_alex.name == "Alex Morgan"
        assert tuple(
            session.scalars(
                select(UserCategorySubscription.category_code)
                .where(UserCategorySubscription.user_id == 1)
                .order_by(UserCategorySubscription.category_code)
            )
        ) == ("finance", "sports")
        assert tuple(
            session.scalars(
                select(UserChannelPreference.channel_code)
                .where(UserChannelPreference.user_id == 2)
                .order_by(UserChannelPreference.channel_code)
            )
        ) == ("sms",)
