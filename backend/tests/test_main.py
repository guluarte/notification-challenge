"""Tests for FastAPI application lifecycle management."""

import asyncio
from unittest.mock import patch

from fastapi import FastAPI

from app.main import create_app


async def _run_lifespan(app: FastAPI) -> None:
    """Enter and exit the app lifespan context once."""

    async with app.router.lifespan_context(app):
        return None


def test_create_app_disposes_engine_on_shutdown() -> None:
    """The FastAPI lifespan should dispose the shared SQLAlchemy engine."""

    app = create_app()

    with patch("app.main.engine.dispose") as dispose_mock:
        asyncio.run(_run_lifespan(app))

    dispose_mock.assert_called_once_with()
