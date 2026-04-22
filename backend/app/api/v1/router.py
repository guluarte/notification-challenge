"""Versioned API router assembly."""

from fastapi import APIRouter

from app.core.config import settings

from .routes.catalog import router as catalog_router
from .routes.health import router as health_router
from .routes.logs import router as logs_router
from .routes.messages import router as messages_router

router = APIRouter(prefix=settings.api_prefix)
router.include_router(health_router)
router.include_router(catalog_router)
router.include_router(messages_router)
router.include_router(logs_router)
