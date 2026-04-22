"""Shared application exception types for consistent API error handling."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base exception for predictable application failures."""

    status_code: int = 400
    code: str = "application_error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ServiceUnavailableError(ApplicationError):
    """Raised when a required dependency or catalog is unavailable."""

    status_code = 503
    code = "service_unavailable"


class InfrastructureError(ApplicationError):
    """Raised when persistence or infrastructure interactions fail."""

    status_code = 500
    code = "infrastructure_error"


class IdempotencyConflictError(ApplicationError):
    """Raised when an idempotency key is reused for a different submission."""

    status_code = 409
    code = "idempotency_conflict"


class StrategyConfigurationError(ApplicationError):
    """Raised when a notification channel cannot be resolved."""

    status_code = 500
    code = "strategy_configuration_error"
