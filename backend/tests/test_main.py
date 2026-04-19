"""Tests for FastAPI application lifecycle management."""

import asyncio
import logging
from unittest.mock import patch

from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI
from uvicorn.logging import DefaultFormatter

from app.core.exceptions import ApplicationError
from app.core.config import BASE_DIR, Settings
from app.main import create_app


async def _run_lifespan(app: FastAPI) -> None:
    """Enter and exit the app lifespan context once."""

    async with app.router.lifespan_context(app):
        return None


def test_create_app_disposes_engine_on_shutdown() -> None:
    """The FastAPI lifespan should dispose the shared SQLAlchemy engine."""

    app = create_app()

    with (
        patch("app.main.configure_logging") as configure_logging_mock,
        patch("app.main.engine.dispose") as dispose_mock,
    ):
        asyncio.run(_run_lifespan(app))

    configure_logging_mock.assert_called_once()
    dispose_mock.assert_called_once_with()


def test_lifespan_configures_app_logging_from_settings() -> None:
    """The lifespan should configure application logging using the settings value."""

    app = create_app()
    app_logger = logging.getLogger("app")
    original_app_handlers = list(app_logger.handlers)
    original_app_propagate = app_logger.propagate
    original_app_level = app_logger.level

    try:
        with patch("app.main.settings.log_level", "debug"):
            asyncio.run(_run_lifespan(app))

        assert len(app_logger.handlers) == 1
        assert isinstance(app_logger.handlers[0].formatter, DefaultFormatter)
        assert app_logger.propagate is False
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.handlers = original_app_handlers
        app_logger.propagate = original_app_propagate
        app_logger.setLevel(original_app_level)


def test_settings_load_env_file_from_backend_directory() -> None:
    """Settings should resolve the env file relative to the backend directory."""

    assert Settings.model_config.get("env_file") == BASE_DIR / ".env"


def test_create_app_registers_shared_exception_handlers() -> None:
    """The app factory should register centralized exception handlers."""

    app = create_app()

    assert ApplicationError in app.exception_handlers
    assert RequestValidationError in app.exception_handlers
    assert Exception in app.exception_handlers
