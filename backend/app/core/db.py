"""Reusable database engine, session factory, and health-check helpers."""

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionFactory: sessionmaker[Session] = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def database_is_healthy(session: Session) -> bool:
    """Return whether the configured database session can answer a trivial query."""

    try:
        return session.scalar(select(1)) == 1
    except SQLAlchemyError:
        return False
