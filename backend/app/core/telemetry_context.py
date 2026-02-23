from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from opentelemetry import trace


@dataclass
class TelemetryContext:
    action_id: str | None = None
    session_id: str | None = None
    attempt_no: int | None = None
    user_id: str | None = None
    email: str | None = None
    feature: str | None = None
    operation: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    message_client_id: str | None = None
    task_retry_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_CURRENT_TELEMETRY: ContextVar[TelemetryContext | None] = ContextVar(
    "current_telemetry", default=None
)


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_attempt_no(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def telemetry_from_headers(headers: Mapping[str, Any]) -> TelemetryContext:
    message_client_id = _clean_str(headers.get("x-message-client-id"))
    subject_id = _clean_str(headers.get("x-subject-id")) or message_client_id
    feature = _clean_str(headers.get("x-feature"))
    subject_type = _clean_str(headers.get("x-subject-type"))
    if not subject_type and (message_client_id or (feature == "chat" and subject_id)):
        subject_type = "chat_message"

    return TelemetryContext(
        action_id=_clean_str(headers.get("x-action-id")),
        session_id=_clean_str(headers.get("x-session-id")),
        attempt_no=parse_attempt_no(headers.get("x-attempt-no")),
        feature=feature,
        operation=_clean_str(headers.get("x-operation")),
        subject_type=subject_type,
        subject_id=subject_id,
        message_client_id=message_client_id,
    )


def telemetry_from_mapping(data: Mapping[str, Any]) -> TelemetryContext:
    message_client_id = _clean_str(data.get("message_client_id"))
    subject_id = _clean_str(data.get("subject_id")) or message_client_id
    feature = _clean_str(data.get("feature"))
    subject_type = _clean_str(data.get("subject_type"))
    if not subject_type and (message_client_id or (feature == "chat" and subject_id)):
        subject_type = "chat_message"

    return TelemetryContext(
        action_id=_clean_str(data.get("action_id")),
        session_id=_clean_str(data.get("session_id")),
        attempt_no=parse_attempt_no(data.get("attempt_no")),
        user_id=_clean_str(data.get("user_id")),
        email=_clean_str(data.get("email")),
        feature=feature,
        operation=_clean_str(data.get("operation")),
        subject_type=subject_type,
        subject_id=subject_id,
        message_client_id=message_client_id,
        task_retry_count=parse_attempt_no(data.get("task_retry_count")),
    )


def merge_telemetry(base: TelemetryContext | None = None, **updates: Any) -> TelemetryContext:
    current = base or TelemetryContext()
    data = current.to_dict()
    for key, value in updates.items():
        if key not in data:
            continue
        if value is None:
            continue
        data[key] = value
    merged = TelemetryContext(**data)

    if not merged.subject_id and merged.message_client_id:
        merged.subject_id = merged.message_client_id
    if not merged.subject_type and merged.subject_id and merged.feature == "chat":
        merged.subject_type = "chat_message"

    return merged


def get_current_telemetry() -> TelemetryContext:
    return _CURRENT_TELEMETRY.get() or TelemetryContext()


def set_current_telemetry(ctx: TelemetryContext) -> Any:
    return _CURRENT_TELEMETRY.set(ctx)


def apply_span_attributes(ctx: TelemetryContext) -> None:
    span = trace.get_current_span()
    if span is None:
        return

    if ctx.action_id:
        span.set_attribute("action.id", ctx.action_id)
    if ctx.session_id:
        span.set_attribute("session.id", ctx.session_id)
    if ctx.user_id:
        span.set_attribute("enduser.id", ctx.user_id)
    if ctx.feature:
        span.set_attribute("app.feature", ctx.feature)
    if ctx.operation:
        span.set_attribute("app.operation", ctx.operation)
    if ctx.subject_type:
        span.set_attribute("app.subject_type", ctx.subject_type)
    if ctx.subject_id:
        span.set_attribute("app.subject_id", ctx.subject_id)
    if ctx.attempt_no is not None:
        span.set_attribute("app.attempt_no", ctx.attempt_no)
    if ctx.message_client_id:
        span.set_attribute("chat.message_client_id", ctx.message_client_id)
    if ctx.task_retry_count is not None:
        span.set_attribute("task.retry_count", ctx.task_retry_count)


@contextmanager
def bind_telemetry(ctx: TelemetryContext):
    token = set_current_telemetry(ctx)
    apply_span_attributes(ctx)
    try:
        yield ctx
    finally:
        _CURRENT_TELEMETRY.reset(token)


def merge_current_telemetry(**updates: Any) -> TelemetryContext:
    ctx = merge_telemetry(get_current_telemetry(), **updates)
    set_current_telemetry(ctx)
    apply_span_attributes(ctx)
    return ctx


def attach_request_telemetry(request: Any, ctx: TelemetryContext) -> TelemetryContext:
    request.state.telemetry = ctx

    # Compatibility aliases while old call sites migrate.
    request.state.action_id = ctx.action_id
    request.state.session_id = ctx.session_id
    request.state.message_client_id = ctx.message_client_id

    return ctx


def get_request_telemetry(request: Any) -> TelemetryContext:
    ctx = getattr(request.state, "telemetry", None)
    if isinstance(ctx, TelemetryContext):
        return ctx
    return TelemetryContext(
        action_id=getattr(request.state, "action_id", None),
        session_id=getattr(request.state, "session_id", None),
        message_client_id=getattr(request.state, "message_client_id", None),
    )


def update_request_telemetry(request: Any, **updates: Any) -> TelemetryContext:
    current = get_request_telemetry(request)
    merged = merge_telemetry(current, **updates)
    attach_request_telemetry(request, merged)
    merge_current_telemetry(**merged.to_dict())
    return merged
