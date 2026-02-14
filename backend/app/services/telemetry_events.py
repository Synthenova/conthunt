from __future__ import annotations

from typing import Any

from app.agent.telemetry.redaction import redact
from app.core.telemetry_context import TelemetryContext
from app.integrations.posthog_client import capture_event


def _distinct_id(ctx: TelemetryContext, user_id: str | None = None) -> str:
    if user_id:
        return user_id
    if ctx.user_id:
        return ctx.user_id
    if ctx.session_id:
        return f"anonymous:{ctx.session_id}"
    return "anonymous"


def _base_props(ctx: TelemetryContext) -> dict[str, Any]:
    return {
        "action_id": ctx.action_id,
        "session_id": ctx.session_id,
        "attempt_no": ctx.attempt_no,
        "user_id": ctx.user_id,
        "feature": ctx.feature,
        "operation": ctx.operation,
        "subject_type": ctx.subject_type,
        "subject_id": ctx.subject_id,
        "message_client_id": ctx.message_client_id,
        "task_retry_count": ctx.task_retry_count,
    }


def emit_action_started(
    ctx: TelemetryContext,
    *,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="action_started",
        properties=redact({**_base_props(ctx), "metadata": metadata or {}}),
    )


def emit_action_succeeded(
    ctx: TelemetryContext,
    *,
    user_id: str | None = None,
    duration_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="action_succeeded",
        properties=redact(
            {
                **_base_props(ctx),
                "duration_ms": duration_ms,
                "metadata": metadata or {},
            }
        ),
    )


def emit_action_failed(
    ctx: TelemetryContext,
    *,
    user_id: str | None = None,
    duration_ms: float | None = None,
    error_kind: str | None = None,
    http_status: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="action_failed",
        properties=redact(
            {
                **_base_props(ctx),
                "duration_ms": duration_ms,
                "error_kind": error_kind,
                "http_status": http_status,
                "metadata": metadata or {},
            }
        ),
    )


def emit_chat_request_received(
    ctx: TelemetryContext,
    *,
    chat_id: str,
    user_id: str | None = None,
) -> bool:
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="chat_request_received",
        properties=redact({**_base_props(ctx), "chat_id": chat_id}),
    )


def emit_chat_stream_server_error(
    ctx: TelemetryContext,
    *,
    chat_id: str,
    error_kind: str,
    user_id: str | None = None,
) -> bool:
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="chat_stream_server_error",
        properties=redact(
            {
                **_base_props(ctx),
                "chat_id": chat_id,
                "error_kind": error_kind,
            }
        ),
    )


def emit_payment_webhook_received(
    *,
    user_id: str | None,
    event_type: str,
    subject_id: str | None,
) -> bool:
    ctx = TelemetryContext(
        feature="billing",
        operation="payment_webhook",
        subject_type="payment_event",
        subject_id=subject_id,
        user_id=user_id,
    )
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="payment_webhook_received",
        properties=redact({**_base_props(ctx), "event_type": event_type}),
    )


def emit_payment_confirmed(
    *,
    user_id: str | None,
    subscription_id: str | None,
    product_id: str | None,
) -> bool:
    ctx = TelemetryContext(
        feature="billing",
        operation="payment_confirmed",
        subject_type="subscription",
        subject_id=subscription_id,
        user_id=user_id,
    )
    return capture_event(
        distinct_id=_distinct_id(ctx, user_id),
        event="payment_confirmed",
        properties=redact(
            {
                **_base_props(ctx),
                "product_id": product_id,
            }
        ),
    )
