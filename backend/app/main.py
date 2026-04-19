"""FastAPI application bootstrap."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router as api_v1_router
from .core import configure_logging, settings
from .core.db import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Dispose pooled database connections when the app shuts down."""

    configure_logging(settings.log_level)
    logger.info(
        "Starting FastAPI application with api_prefix=%s cors_origins=%s log_level=%s",
        settings.api_prefix,
        settings.cors_origin_list(),
        settings.log_level,
    )

    try:
        yield
    finally:
        logger.info("Disposing database engine during application shutdown")
        engine.dispose()


def create_app() -> FastAPI:
    """Create the configured FastAPI application instance."""

    application = FastAPI(title=settings.app_name, lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_v1_router)

    return application


app = create_app()
