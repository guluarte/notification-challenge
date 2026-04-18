"""FastAPI application bootstrap."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router as api_v1_router
from .core.config import settings
from .core.db import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Dispose pooled database connections when the app shuts down."""

    try:
        yield
    finally:
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

    application.include_router(api_v1_router, prefix=settings.api_prefix)

    return application


app = create_app()
