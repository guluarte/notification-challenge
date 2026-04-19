"""Logging configuration helpers for the backend application."""

import logging

from uvicorn.logging import DefaultFormatter


def resolve_log_level(log_level: str) -> int:
    """Map a string log level to the corresponding stdlib logging constant."""

    return getattr(logging, log_level.upper(), logging.INFO)


def configure_logging(log_level: str) -> None:
    """Configure application loggers to emit using Uvicorn-style formatting."""

    resolved_level = resolve_log_level(log_level)
    app_logger = logging.getLogger("app")
    handler = logging.StreamHandler()
    handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))

    app_logger.handlers = [handler]
    app_logger.propagate = False
    app_logger.setLevel(resolved_level)
    logging.getLogger("uvicorn.error").setLevel(resolved_level)
    logging.getLogger("uvicorn.access").setLevel(resolved_level)
