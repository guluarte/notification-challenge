"""Route-level tests for catalog, message, and log endpoints."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any

from starlette.types import Message, Scope

from app.api.dependencies import (
    get_message_service,
    get_notification_catalog_service,
    get_notification_log_service,
)
from app.core.exceptions import (
    IdempotencyConflictError,
    InfrastructureError,
    ServiceUnavailableError,
)
from app.main import create_app
from app.models.enums import DeliveryStatus
from app.services.types import (
    MessageCreationResult,
    NotificationCatalog,
    NotificationCatalogItem,
    NotificationLogEntry,
    NotificationLogPage,
)


async def _call_app(
    *,
    method: str,
    path: str,
    query_string: str = "",
    json_body: dict[str, object] | None = None,
    extra_headers: dict[str, str] | None = None,
    app_overrides: dict[Callable[..., Any], Callable[..., Any]] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Issue a minimal ASGI request against the FastAPI app."""

    app = create_app()
    if app_overrides is not None:
        for dependency, override in app_overrides.items():
            app.dependency_overrides[dependency] = override

    request_body = b""
    headers: list[tuple[bytes, bytes]] = []
    if json_body is not None:
        request_body = json.dumps(json_body).encode("utf-8")
        headers.append((b"content-type", b"application/json"))
        headers.append((b"content-length", str(len(request_body)).encode("ascii")))
    if extra_headers is not None:
        for name, value in extra_headers.items():
            headers.append((name.lower().encode("ascii"), value.encode("ascii")))

    raw_path = path
    if query_string != "":
        raw_path = f"{path}?{query_string}"

    scope: Scope = {
        "type": "http",
        "http_version": "1.1",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": raw_path.encode("ascii"),
        "query_string": query_string.encode("ascii"),
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "root_path": "",
    }

    body_sent = False
    response_status = 500
    response_body = bytearray()

    async def receive() -> Message:
        nonlocal body_sent
        if body_sent:
            return {"type": "http.disconnect"}
        body_sent = True
        return {"type": "http.request", "body": request_body, "more_body": False}

    async def send(message: Message) -> None:
        nonlocal response_status
        if message["type"] == "http.response.start":
            status = message["status"]
            if isinstance(status, int):
                response_status = status
        if message["type"] == "http.response.body":
            body = message.get("body", b"")
            if isinstance(body, bytes):
                response_body.extend(body)

    try:
        try:
            await app(scope, receive, send)
        except Exception:
            if not response_body:
                raise
    finally:
        app.dependency_overrides.clear()

    return response_status, json.loads(response_body.decode("utf-8"))


def _isoformat_z(value: datetime) -> str:
    """Return the JSON datetime representation emitted by FastAPI."""

    return value.isoformat().replace("+00:00", "Z")


@dataclass
class FakeMessageService:
    """Message service double for route tests."""

    result: MessageCreationResult | None = None
    error: Exception | None = None
    last_call: tuple[str, str, str | None] | None = None

    def create_message(
        self,
        *,
        category_code: str,
        body: str,
        idempotency_key: str | None = None,
    ) -> MessageCreationResult:
        self.last_call = (category_code, body, idempotency_key)
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("Expected a message result")
        return self.result


class FakeNotificationLogService:
    """Log service double for route tests."""

    def __init__(
        self,
        entries: list[NotificationLogEntry],
        *,
        error: Exception | None = None,
    ) -> None:
        self.entries = entries
        self.error = error
        self.calls: list[tuple[int, int]] = []

    def list_logs(self, *, limit: int = 10, offset: int = 0) -> NotificationLogPage:
        self.calls.append((limit, offset))
        if self.error is not None:
            raise self.error
        return NotificationLogPage(
            items=self.entries,
            total=25,
            limit=limit,
            offset=offset,
        )


@dataclass
class FakeNotificationCatalogService:
    """Catalog service double for route tests."""

    catalog: NotificationCatalog

    def get_catalog(self) -> NotificationCatalog:
        """Return the configured catalog response."""

        return self.catalog


def _message_service_override(
    service: FakeMessageService,
) -> Callable[[], FakeMessageService]:
    return lambda: service


def _log_service_override(
    service: FakeNotificationLogService,
) -> Callable[[], FakeNotificationLogService]:
    return lambda: service


def _catalog_service_override(
    service: FakeNotificationCatalogService,
) -> Callable[[], FakeNotificationCatalogService]:
    return lambda: service


def test_catalog_route_returns_backend_supported_options() -> None:
    """The route should expose categories and channels from the catalog service."""

    service = FakeNotificationCatalogService(
        catalog=NotificationCatalog(
            categories=[
                NotificationCatalogItem(code="sports", label="Sports"),
                NotificationCatalogItem(code="finance", label="Finance"),
                NotificationCatalogItem(code="movies", label="Movies"),
            ],
            channels=[
                NotificationCatalogItem(code="sms", label="SMS"),
                NotificationCatalogItem(code="email", label="E-Mail"),
                NotificationCatalogItem(code="push", label="Push Notification"),
            ],
        )
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="GET",
            path="/v1/catalog",
            app_overrides={
                get_notification_catalog_service: _catalog_service_override(service)
            },
        )
    )

    assert status_code == 200
    assert payload == {
        "categories": [
            {"code": "sports", "label": "Sports"},
            {"code": "finance", "label": "Finance"},
            {"code": "movies", "label": "Movies"},
        ],
        "channels": [
            {"code": "sms", "label": "SMS"},
            {"code": "email", "label": "E-Mail"},
            {"code": "push", "label": "Push Notification"},
        ],
    }


def test_create_message_route_returns_created_payload() -> None:
    """The route should map the message service result into the response DTO."""

    created_at = datetime.now(tz=timezone.utc)
    service = FakeMessageService(
        result=MessageCreationResult(
            message_id=12,
            category_code="sports",
            body="Team A won",
            total_users=2,
            total_attempts=3,
            sent=2,
            failed=1,
            created_at=created_at,
        )
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "sports", "body": "  Team A won  "},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 201
    assert payload == {
        "message_id": 12,
        "category": "sports",
        "body": "Team A won",
        "total_users": 2,
        "total_attempts": 3,
        "sent": 2,
        "failed": 1,
        "created_at": _isoformat_z(created_at),
    }
    assert service.last_call == ("sports", "Team A won", None)


def test_create_message_route_passes_idempotency_key_header() -> None:
    """The route should pass normalized idempotency keys into the service."""

    created_at = datetime.now(tz=timezone.utc)
    service = FakeMessageService(
        result=MessageCreationResult(
            message_id=12,
            category_code="sports",
            body="Team A won",
            total_users=2,
            total_attempts=3,
            sent=2,
            failed=1,
            created_at=created_at,
        )
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "sports", "body": "Team A won"},
            extra_headers={"Idempotency-Key": " submit-123 "},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 201
    assert payload["message_id"] == 12
    assert service.last_call == ("sports", "Team A won", "submit-123")


def test_create_message_route_returns_ok_for_idempotent_duplicate() -> None:
    """Duplicate idempotent submissions should replay the prior result."""

    created_at = datetime.now(tz=timezone.utc)
    service = FakeMessageService(
        result=MessageCreationResult(
            message_id=12,
            category_code="sports",
            body="Team A won",
            total_users=2,
            total_attempts=3,
            sent=2,
            failed=1,
            created_at=created_at,
            idempotency_key="submit-123",
            was_duplicate=True,
        )
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "sports", "body": "Team A won"},
            extra_headers={"Idempotency-Key": "submit-123"},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 200
    assert payload == {
        "message_id": 12,
        "category": "sports",
        "body": "Team A won",
        "total_users": 2,
        "total_attempts": 3,
        "sent": 2,
        "failed": 1,
        "created_at": _isoformat_z(created_at),
    }
    assert service.last_call == ("sports", "Team A won", "submit-123")


def test_create_message_route_returns_validation_payload_for_blank_body() -> None:
    """Blank message bodies should return the centralized validation response."""

    service = FakeMessageService()

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "sports", "body": "   "},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 422
    assert payload["detail"] == "Request validation failed."
    assert payload["code"] == "validation_error"
    assert payload["errors"] == [
        {
            "field": "body",
            "message": "Value error, Message body must not be blank.",
        }
    ]
    assert service.last_call is None


def test_create_message_route_returns_validation_payload_for_invalid_category() -> None:
    """Unsupported categories should return the centralized validation response."""

    service = FakeMessageService()

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "weather", "body": "Forecast"},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 422
    assert payload["detail"] == "Request validation failed."
    assert payload["code"] == "validation_error"
    assert payload["errors"] == [
        {
            "field": "category",
            "message": "Input should be 'sports', 'finance' or 'movies'",
        }
    ]
    assert service.last_call is None


def test_create_message_route_maps_application_errors() -> None:
    """Known application errors should use the centralized error payload."""

    service = FakeMessageService(
        error=ServiceUnavailableError(
            "The notification category catalog is unavailable."
        )
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "finance", "body": "Quarterly update"},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 503
    assert payload == {
        "detail": "The notification category catalog is unavailable.",
        "code": "service_unavailable",
    }


def test_create_message_route_maps_idempotency_conflicts() -> None:
    """Idempotency key reuse with a different payload should return 409."""

    service = FakeMessageService(
        error=IdempotencyConflictError(
            "The idempotency key has already been used for a different message."
        )
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "finance", "body": "Quarterly update"},
            extra_headers={"Idempotency-Key": "submit-123"},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 409
    assert payload == {
        "detail": "The idempotency key has already been used for a different message.",
        "code": "idempotency_conflict",
    }


def test_create_message_route_maps_infrastructure_errors() -> None:
    """Infrastructure application errors should return their explicit payload."""

    service = FakeMessageService(
        error=InfrastructureError("The message could not be persisted.")
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "movies", "body": "Premiere tonight"},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 500
    assert payload == {
        "detail": "The message could not be persisted.",
        "code": "infrastructure_error",
    }


def test_create_message_route_maps_unexpected_errors_to_internal_server_error() -> None:
    """Unexpected route failures should return the generic error payload."""

    service = FakeMessageService(error=RuntimeError("boom"))

    status_code, payload = asyncio.run(
        _call_app(
            method="POST",
            path="/v1/messages",
            json_body={"category": "movies", "body": "Premiere tonight"},
            app_overrides={get_message_service: _message_service_override(service)},
        )
    )

    assert status_code == 500
    assert payload == {
        "detail": "Internal server error.",
        "code": "internal_server_error",
    }


def test_logs_route_returns_log_items() -> None:
    """The logs route should expose delivery history through DTOs."""

    attempted_at = datetime.now(tz=timezone.utc)
    processing_started_at = datetime.now(tz=timezone.utc)
    processed_at = datetime.now(tz=timezone.utc)
    delivered_at = datetime.now(tz=timezone.utc)
    service = FakeNotificationLogService(
        entries=[
            NotificationLogEntry(
                attempt_id=9,
                message_id=4,
                category_code="sports",
                body="Team A won",
                user_id=1,
                user_name="Alex",
                user_email="alex@example.com",
                user_phone_number="+15550000001",
                channel_code="email",
                status=DeliveryStatus.SENT,
                attempt_number=1,
                attempted_at=attempted_at,
                processing_started_at=processing_started_at,
                processed_at=processed_at,
                delivered_at=delivered_at,
                last_error_at=None,
                next_retry_at=None,
                failure_reason=None,
                provider_reference="email-4-1",
            )
        ]
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="GET",
            path="/v1/logs",
            app_overrides={
                get_notification_log_service: _log_service_override(service)
            },
        )
    )

    assert status_code == 200
    assert payload == {
        "items": [
            {
                "attempt_id": 9,
                "message_id": 4,
                "category": "sports",
                "body": "Team A won",
                "user": {
                    "id": 1,
                    "name": "Alex",
                    "email": "alex@example.com",
                    "phone_number": "+15550000001",
                },
                "channel": "email",
                "status": "sent",
                "attempt_number": 1,
                "attempted_at": _isoformat_z(attempted_at),
                "processing_started_at": _isoformat_z(processing_started_at),
                "processed_at": _isoformat_z(processed_at),
                "delivered_at": _isoformat_z(delivered_at),
                "last_error_at": None,
                "next_retry_at": None,
                "failure_reason": None,
                "provider_reference": "email-4-1",
            }
        ],
        "total": 25,
        "limit": 10,
        "offset": 0,
    }
    assert service.calls == [(10, 0)]


def test_logs_route_accepts_pagination_query_parameters() -> None:
    """The logs route should pass page sizing through to the service layer."""

    service = FakeNotificationLogService(entries=[])

    status_code, payload = asyncio.run(
        _call_app(
            method="GET",
            path="/v1/logs",
            query_string="limit=50&offset=100",
            app_overrides={
                get_notification_log_service: _log_service_override(service)
            },
        )
    )

    assert status_code == 200
    assert payload == {"items": [], "total": 25, "limit": 50, "offset": 100}
    assert service.calls == [(50, 100)]


def test_logs_route_maps_infrastructure_errors() -> None:
    """Infrastructure failures should use the shared error response contract."""

    service = FakeNotificationLogService(
        entries=[],
        error=InfrastructureError("The notification logs could not be loaded."),
    )

    status_code, payload = asyncio.run(
        _call_app(
            method="GET",
            path="/v1/logs",
            app_overrides={
                get_notification_log_service: _log_service_override(service)
            },
        )
    )

    assert status_code == 500
    assert payload == {
        "detail": "The notification logs could not be loaded.",
        "code": "infrastructure_error",
    }
