"""Route-level tests for message and log endpoints."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any, cast

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.dependencies import get_message_service, get_notification_log_service
from app.core.exceptions import InfrastructureError, ServiceUnavailableError
from app.main import create_app
from app.models.enums import DeliveryStatus
from app.services.types import MessageCreationResult, NotificationLogEntry


async def _call_app(
    *,
    method: str,
    path: str,
    json_body: dict[str, object] | None = None,
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

    scope: Scope = {
        "type": "http",
        "http_version": "1.1",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
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
            return cast(Message, {"type": "http.disconnect"})
        body_sent = True
        return cast(
            Message,
            {"type": "http.request", "body": request_body, "more_body": False},
        )

    async def send(message: Message) -> None:
        nonlocal response_status
        if message["type"] == "http.response.start":
            response_status = cast(int, message["status"])
        if message["type"] == "http.response.body":
            response_body.extend(cast(bytes, message.get("body", b"")))

    try:
        asgi_app = cast(ASGIApp, app)
        try:
            await asgi_app(scope, cast(Receive, receive), cast(Send, send))
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
    last_call: tuple[str, str] | None = None

    def create_message(self, *, category_code: str, body: str) -> MessageCreationResult:
        self.last_call = (category_code, body)
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
        self.calls = 0

    def list_logs(self) -> list[NotificationLogEntry]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.entries


def _message_service_override(
    service: FakeMessageService,
) -> Callable[[], FakeMessageService]:
    return lambda: service


def _log_service_override(
    service: FakeNotificationLogService,
) -> Callable[[], FakeNotificationLogService]:
    return lambda: service


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
    assert service.last_call == ("sports", "Team A won")


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
        ]
    }
    assert service.calls == 1


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
