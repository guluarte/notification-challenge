INSERT INTO seed_users (
    id,
    name,
    email,
    phone_number,
    categories,
    channels
)
VALUES
    (
        1,
        'Alex Morgan',
        'alex.morgan@example.com',
        '+15550001001',
        '["Sports", "Movies"]'::jsonb,
        '["E-Mail", "Push Notification"]'::jsonb
    ),
    (
        2,
        'Jordan Lee',
        'jordan.lee@example.com',
        '+15550001002',
        '["Finance"]'::jsonb,
        '["SMS", "E-Mail"]'::jsonb
    ),
    (
        3,
        'Sam Rivera',
        'sam.rivera@example.com',
        '+15550001003',
        '["Sports", "Finance", "Movies"]'::jsonb,
        '["SMS", "E-Mail", "Push Notification"]'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    phone_number = EXCLUDED.phone_number,
    categories = EXCLUDED.categories,
    channels = EXCLUDED.channels;

INSERT INTO notification_categories (
    code,
    name
)
VALUES
    ('sports', 'Sports'),
    ('finance', 'Finance'),
    ('movies', 'Movies')
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name;

INSERT INTO notification_channels (
    code,
    name
)
VALUES
    ('sms', 'SMS'),
    ('email', 'E-Mail'),
    ('push', 'Push Notification')
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name;

INSERT INTO users (
    id,
    name,
    email,
    phone_number
)
SELECT
    id,
    name,
    email,
    phone_number
FROM seed_users
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    phone_number = EXCLUDED.phone_number;

SELECT setval(
    pg_get_serial_sequence('users', 'id'),
    COALESCE((SELECT MAX(id) FROM users), 1),
    true
);

DELETE FROM user_category_subscriptions
WHERE user_id IN (SELECT id FROM seed_users);

INSERT INTO user_category_subscriptions (
    user_id,
    category_code
)
SELECT
    seed_user.id,
    category_catalog.code
FROM seed_users AS seed_user
CROSS JOIN LATERAL jsonb_array_elements_text(seed_user.categories) AS seeded_category(name)
JOIN notification_categories AS category_catalog
    ON category_catalog.name = seeded_category.name;

DELETE FROM user_channel_preferences
WHERE user_id IN (SELECT id FROM seed_users);

INSERT INTO user_channel_preferences (
    user_id,
    channel_code
)
SELECT
    seed_user.id,
    channel_catalog.code
FROM seed_users AS seed_user
CROSS JOIN LATERAL jsonb_array_elements_text(seed_user.channels) AS seeded_channel(name)
JOIN notification_channels AS channel_catalog
    ON channel_catalog.name = seeded_channel.name;
