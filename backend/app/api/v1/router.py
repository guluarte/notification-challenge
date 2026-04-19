"""Versioned API router assembly."""

from fastapi import APIRouter

from app.core.config import settings

from .routes.health import router as health_router

router = APIRouter(prefix=settings.api_prefix)
router.include_router(health_router)
