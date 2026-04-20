"""FastAPI application bootstrap."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.router import router as api_v1_router
from .core import configure_logging, settings
from .core.db import engine
from .core.exceptions import ApplicationError
from .schemas.dtos import (
    ErrorResponseDTO,
    ValidationErrorItemDTO,
    ValidationErrorResponseDTO,
)

logger = logging.getLogger(__name__)


def _validation_error_field(location: tuple[int | str, ...]) -> str:
    """Return a stable field path for validation errors."""

    transport_markers = {"body", "query", "path"}
    path_parts = [str(part) for part in location]

    while len(path_parts) > 1 and path_parts[0] in transport_markers:
        path_parts = path_parts[1:]

    if len(path_parts) == 0:
        return "request"

    return ".".join(path_parts)


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

    application.add_exception_handler(ApplicationError, handle_application_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(Exception, handle_unexpected_error)
    application.include_router(api_v1_router)

    return application


async def handle_application_error(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    """Return the standard payload for known application errors."""

    if not isinstance(exc, ApplicationError):
        logger.exception("Non-application error routed to application handler")
        payload = ErrorResponseDTO(
            detail="Internal server error.",
            code="internal_server_error",
        )
        return JSONResponse(status_code=500, content=payload.model_dump())

    application_error = exc
    logger.warning(
        "Handled application error code=%s detail=%s",
        application_error.code,
        application_error.detail,
    )
    payload = ErrorResponseDTO(
        detail=application_error.detail,
        code=application_error.code,
    )
    return JSONResponse(
        status_code=application_error.status_code,
        content=payload.model_dump(),
    )


async def handle_validation_error(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a predictable payload for request validation failures."""

    if not isinstance(exc, RequestValidationError):
        logger.exception("Non-validation error routed to validation handler")
        payload = ErrorResponseDTO(
            detail="Internal server error.",
            code="internal_server_error",
        )
        return JSONResponse(status_code=500, content=payload.model_dump())

    validation_error = exc
    logger.warning(
        "Request validation failed with %s errors",
        len(validation_error.errors()),
    )
    errors = [
        ValidationErrorItemDTO(
            field=_validation_error_field(error["loc"]),
            message=str(error["msg"]),
        )
        for error in validation_error.errors()
    ]
    payload = ValidationErrorResponseDTO(
        detail="Request validation failed.",
        code="validation_error",
        errors=errors,
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    """Return a safe payload for unhandled server errors."""

    logger.exception("Unhandled request failure", exc_info=exc)
    payload = ErrorResponseDTO(
        detail="Internal server error.",
        code="internal_server_error",
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


app = create_app()
