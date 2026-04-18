"""FastAPI dependencies for database-backed request handling."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import SessionFactory


def get_db_session() -> Generator[Session, None, None]:
    """Yield a request-scoped ORM session and roll back on handler errors."""

    with SessionFactory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


DBSessionDep = Annotated[Session, Depends(get_db_session)]
