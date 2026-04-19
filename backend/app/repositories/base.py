"""Shared repository helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepository:
    """Base repository storing the current SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self.session = session
