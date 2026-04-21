from sqlalchemy import Table

from app.models.enums import (
    DELIVERY_STATUS_VALUES,
    MESSAGE_CATEGORY_CATALOG,
    MESSAGE_CATEGORY_CODES,
    MESSAGE_CATEGORY_LABELS_BY_CODE,
    NOTIFICATION_CHANNEL_CATALOG,
    NOTIFICATION_CHANNEL_CODES,
    NOTIFICATION_CHANNEL_LABELS_BY_CODE,
)
from app.models.user_category_subscription import UserCategorySubscription
from app.models.user_channel_preference import UserChannelPreference


def test_message_category_catalog_defines_exact_task_scope() -> None:
    assert tuple(entry.code.value for entry in MESSAGE_CATEGORY_CATALOG) == (
        "sports",
        "finance",
        "movies",
    )
    assert tuple(entry.label.value for entry in MESSAGE_CATEGORY_CATALOG) == (
        "Sports",
        "Finance",
        "Movies",
    )
    assert tuple(code.value for code in MESSAGE_CATEGORY_CODES) == (
        "sports",
        "finance",
        "movies",
    )
    assert {
        code.value: label.value
        for code, label in MESSAGE_CATEGORY_LABELS_BY_CODE.items()
    } == {
        "sports": "Sports",
        "finance": "Finance",
        "movies": "Movies",
    }


def test_notification_channel_catalog_defines_exact_task_scope() -> None:
    assert tuple(entry.code.value for entry in NOTIFICATION_CHANNEL_CATALOG) == (
        "sms",
        "email",
        "push",
    )
    assert tuple(entry.label.value for entry in NOTIFICATION_CHANNEL_CATALOG) == (
        "SMS",
        "E-Mail",
        "Push Notification",
    )
    assert tuple(code.value for code in NOTIFICATION_CHANNEL_CODES) == (
        "sms",
        "email",
        "push",
    )
    assert {
        code.value: label.value
        for code, label in NOTIFICATION_CHANNEL_LABELS_BY_CODE.items()
    } == {
        "sms": "SMS",
        "email": "E-Mail",
        "push": "Push Notification",
    }


def test_delivery_status_values_cover_pending_sent_and_failed() -> None:
    assert DELIVERY_STATUS_VALUES == ("pending", "sent", "failed")


def test_subscription_tables_keep_lookup_indexes_declared_in_orm() -> None:
    category_table = UserCategorySubscription.__table__
    channel_table = UserChannelPreference.__table__

    assert isinstance(category_table, Table)
    assert isinstance(channel_table, Table)

    category_index_names = {
        index_name
        for index in category_table.indexes
        if (index_name := index.name) is not None
    }
    channel_index_names = {
        index_name
        for index in channel_table.indexes
        if (index_name := index.name) is not None
    }

    assert "ix_user_category_subscriptions_category_code" in category_index_names
    assert "ix_user_channel_preferences_channel_code" in channel_index_names
