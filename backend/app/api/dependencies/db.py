"""FastAPI dependencies for database-backed request handling."""

from collections.abc import Generator
import logging
from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.core.db import SessionFactory
from app.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a request-scoped ORM session and roll back on handler errors."""

    with SessionFactory() as session:
        try:
            yield session
        except (ApplicationError, RequestValidationError):
            session.rollback()
            raise
        except Exception:
            logger.exception(
                "Rolling back request-scoped database session after handler failure"
            )
            session.rollback()
            raise


DBSessionDep = Annotated[Session, Depends(get_db_session)]
