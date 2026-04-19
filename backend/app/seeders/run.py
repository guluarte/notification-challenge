"""CLI entry point for deterministic database seeding."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core import configure_logging, settings
from app.core.db import SessionFactory, engine
from app.seeders.demo import seed_database

logger = logging.getLogger(__name__)


def main() -> int:
    """Run the canonical seed flow and return a process exit code."""

    configure_logging(settings.log_level)
    logger.info("Starting database seed run app_env=%s", settings.app_env)

    try:
        with SessionFactory() as session:
            summary = seed_database(session)
            session.commit()
    except SQLAlchemyError:
        logger.exception("Database seed run failed because of a SQLAlchemy error")
        return 1
    except Exception:
        logger.exception("Database seed run failed because of an unexpected error")
        return 1
    finally:
        logger.info("Disposing database engine after seed run")
        engine.dispose()

    logger.info(
        "Database seed run completed categories=%s channels=%s users=%s category_subscriptions=%s channel_preferences=%s",
        summary.categories,
        summary.channels,
        summary.users,
        summary.category_subscriptions,
        summary.channel_preferences,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
