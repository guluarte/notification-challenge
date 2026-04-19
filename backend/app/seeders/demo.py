"""Deterministic database seeders for local and Docker environments."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from app.models import (
    MESSAGE_CATEGORY_CATALOG,
    NOTIFICATION_CHANNEL_CATALOG,
    MessageCategoryCode,
    NotificationCategory,
    NotificationChannel,
    NotificationChannelCode,
    User,
    UserCategorySubscription,
    UserChannelPreference,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SeedUserDefinition:
    """Canonical demo user definition for repeatable seeding."""

    id: int
    name: str
    email: str
    phone_number: str
    category_codes: tuple[MessageCategoryCode, ...]
    channel_codes: tuple[NotificationChannelCode, ...]


@dataclass(frozen=True, slots=True)
class SeedSummary:
    """Counts emitted after a successful seed run."""

    categories: int
    channels: int
    users: int
    category_subscriptions: int
    channel_preferences: int


DEMO_USERS: tuple[SeedUserDefinition, ...] = (
    SeedUserDefinition(
        id=1,
        name="Alex Morgan",
        email="alex.morgan@example.com",
        phone_number="+15550001001",
        category_codes=(
            MessageCategoryCode.SPORTS,
            MessageCategoryCode.FINANCE,
        ),
        channel_codes=(
            NotificationChannelCode.EMAIL,
            NotificationChannelCode.PUSH,
        ),
    ),
    SeedUserDefinition(
        id=2,
        name="Jordan Lee",
        email="jordan.lee@example.com",
        phone_number="+15550001002",
        category_codes=(MessageCategoryCode.MOVIES,),
        channel_codes=(NotificationChannelCode.SMS,),
    ),
    SeedUserDefinition(
        id=3,
        name="Sam Rivera",
        email="sam.rivera@example.com",
        phone_number="+15550001003",
        category_codes=(
            MessageCategoryCode.SPORTS,
            MessageCategoryCode.FINANCE,
            MessageCategoryCode.MOVIES,
        ),
        channel_codes=(
            NotificationChannelCode.SMS,
            NotificationChannelCode.EMAIL,
            NotificationChannelCode.PUSH,
        ),
    ),
    SeedUserDefinition(
        id=4,
        name="Casey Patel",
        email="casey.patel@example.com",
        phone_number="+15550001004",
        category_codes=(
            MessageCategoryCode.FINANCE,
            MessageCategoryCode.MOVIES,
        ),
        channel_codes=(NotificationChannelCode.EMAIL,),
    ),
)


def seed_database(session: Session) -> SeedSummary:
    """Populate canonical catalogs, users, and preference rows."""

    logger.info("Seeding notification category catalog entries")
    for entry in MESSAGE_CATEGORY_CATALOG:
        category = session.get(NotificationCategory, entry.code.value)
        if category is None:
            session.add(
                NotificationCategory(
                    code=entry.code.value,
                    name=entry.label.value,
                )
            )
            continue
        category.name = entry.label.value

    logger.info("Seeding notification channel catalog entries")
    for entry in NOTIFICATION_CHANNEL_CATALOG:
        channel = session.get(NotificationChannel, entry.code.value)
        if channel is None:
            session.add(
                NotificationChannel(
                    code=entry.code.value,
                    name=entry.label.value,
                )
            )
            continue
        channel.name = entry.label.value

    logger.info("Seeding demo notification users")
    for seeded_user in DEMO_USERS:
        user = session.get(User, seeded_user.id)
        if user is None:
            session.add(
                User(
                    id=seeded_user.id,
                    name=seeded_user.name,
                    email=seeded_user.email,
                    phone_number=seeded_user.phone_number,
                )
            )
            continue

        user.name = seeded_user.name
        user.email = seeded_user.email
        user.phone_number = seeded_user.phone_number

    session.flush()

    seeded_user_ids = tuple(seed_user.id for seed_user in DEMO_USERS)
    logger.info(
        "Replacing seeded user subscriptions and channel preferences user_count=%s",
        len(seeded_user_ids),
    )
    session.execute(
        delete(UserCategorySubscription).where(
            UserCategorySubscription.user_id.in_(seeded_user_ids)
        )
    )
    session.execute(
        delete(UserChannelPreference).where(
            UserChannelPreference.user_id.in_(seeded_user_ids)
        )
    )

    session.add_all(
        UserCategorySubscription(
            user_id=seeded_user.id,
            category_code=category_code.value,
        )
        for seeded_user in DEMO_USERS
        for category_code in seeded_user.category_codes
    )
    session.add_all(
        UserChannelPreference(
            user_id=seeded_user.id,
            channel_code=channel_code.value,
        )
        for seeded_user in DEMO_USERS
        for channel_code in seeded_user.channel_codes
    )

    _synchronize_user_identity_sequence(session)

    summary = SeedSummary(
        categories=len(MESSAGE_CATEGORY_CATALOG),
        channels=len(NOTIFICATION_CHANNEL_CATALOG),
        users=len(DEMO_USERS),
        category_subscriptions=sum(
            len(seeded_user.category_codes) for seeded_user in DEMO_USERS
        ),
        channel_preferences=sum(
            len(seeded_user.channel_codes) for seeded_user in DEMO_USERS
        ),
    )
    logger.info(
        "Seed data prepared categories=%s channels=%s users=%s category_subscriptions=%s channel_preferences=%s",
        summary.categories,
        summary.channels,
        summary.users,
        summary.category_subscriptions,
        summary.channel_preferences,
    )
    return summary


def _synchronize_user_identity_sequence(session: Session) -> None:
    """Advance the Postgres identity sequence after explicit seeded IDs."""

    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return

    session.execute(
        text(
            "SELECT setval("
            "pg_get_serial_sequence('users', 'id'), "
            ":seeded_user_id, "
            "true"
            ")"
        ),
        {"seeded_user_id": max(seeded_user.id for seeded_user in DEMO_USERS)},
    )
