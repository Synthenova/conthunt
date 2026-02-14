from __future__ import annotations

from contextlib import nullcontext
import os
import time
from dataclasses import dataclass
from typing import Any

from app.agent.telemetry.redaction import redact
from app.core import get_settings, logger
try:
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
except Exception:  # pragma: no cover
    TracerProvider = None

try:
    from langfuse import Langfuse  # type: ignore
except Exception:  # pragma: no cover
    Langfuse = None

try:
    from langfuse import propagate_attributes  # type: ignore
except Exception:  # pragma: no cover
    propagate_attributes = None

try:
    from langfuse.langchain import CallbackHandler  # type: ignore
except Exception:  # pragma: no cover
    CallbackHandler = None


_langfuse_client = None
_langfuse_tracer_provider = None


@dataclass
class AgentRunContext:
    action_id: str | None
    session_id: str | None
    attempt_no: int | None
    user_id: str | None
    feature: str
    operation: str
    subject_type: str | None
    subject_id: str | None
    conversation_id: str | None = None
    message_client_id: str | None = None
    message_id: str | None = None

    def metadata(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "attempt_no": self.attempt_no,
            "user_id": self.user_id,
            "feature": self.feature,
            "operation": self.operation,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "conversation_id": self.conversation_id,
            "message_client_id": self.message_client_id,
            "message_id": self.message_id,
        }


@dataclass
class LangfuseTraceHandle:
    run_context: AgentRunContext
    started_at: float
    trace: Any | None = None


def is_langfuse_enabled() -> bool:
    settings = get_settings()
    return bool(
        getattr(settings, "TELEMETRY_LANGFUSE_ENABLED", True)
        and settings.LANGFUSE_PUBLIC_KEY
        and settings.LANGFUSE_SECRET_KEY
    )


def _get_langfuse_client() -> Any | None:
    global _langfuse_client, _langfuse_tracer_provider

    if _langfuse_client is not None:
        return _langfuse_client

    if not is_langfuse_enabled() or Langfuse is None:
        return None

    settings = get_settings()
    _sync_langfuse_env(settings)
    try:
        if _langfuse_tracer_provider is None and TracerProvider is not None:
            # Keep Langfuse on its own tracer provider so generic app HTTP spans
            # are not mirrored into Langfuse unless explicitly instrumented.
            _langfuse_tracer_provider = TracerProvider()
        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST or None,
            tracer_provider=_langfuse_tracer_provider,
        )
    except Exception as exc:
        logger.warning("Failed to initialize Langfuse client: %s", exc)
        _langfuse_client = None

    return _langfuse_client


def get_langfuse_client() -> Any | None:
    return _get_langfuse_client()


def _sync_langfuse_env(settings: Any) -> None:
    """Ensure SDKs that read process env can resolve Langfuse credentials."""
    if settings.LANGFUSE_PUBLIC_KEY:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    if settings.LANGFUSE_SECRET_KEY:
        os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    if settings.LANGFUSE_HOST:
        os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
        os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_HOST


def get_langfuse_callback_handler() -> Any | None:
    if not is_langfuse_enabled() or CallbackHandler is None:
        return None

    settings = get_settings()
    _sync_langfuse_env(settings)
    client = _get_langfuse_client()
    if client is None:
        return None

    try:
        # Bind handler to the configured project key instead of relying on ambient env vars.
        return CallbackHandler(public_key=settings.LANGFUSE_PUBLIC_KEY, update_trace=True)
    except TypeError:
        # Backward compatibility for older SDK signatures.
        return CallbackHandler()
    except Exception as exc:
        logger.warning("Failed to create Langfuse callback handler: %s", exc)
        return None


def get_langfuse_propagation_context(
    *,
    user_id: str | None,
    session_id: str | None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    trace_name: str | None = None,
):
    if not is_langfuse_enabled() or propagate_attributes is None:
        return nullcontext()

    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    if session_id:
        kwargs["session_id"] = session_id
    if tags:
        kwargs["tags"] = tags
    if metadata:
        kwargs["metadata"] = redact(metadata)
    if trace_name:
        kwargs["trace_name"] = trace_name

    if not kwargs:
        return nullcontext()

    try:
        return propagate_attributes(**kwargs)
    except Exception as exc:
        logger.debug("Langfuse propagate_attributes disabled: %s", exc)
        return nullcontext()


def start_langfuse_root_observation(
    *,
    name: str,
    input_payload: Any | None = None,
    metadata: dict[str, Any] | None = None,
):
    client = _get_langfuse_client()
    if client is None:
        return nullcontext(None)
    try:
        return client.start_as_current_observation(
            as_type="span",
            name=name,
            input=redact(input_payload) if input_payload is not None else None,
            metadata=redact(metadata or {}),
        )
    except Exception as exc:
        logger.debug("Langfuse start_as_current_observation disabled: %s", exc)
        return nullcontext(None)


def start_trace(run_context: AgentRunContext, tags: list[str] | None = None) -> LangfuseTraceHandle:
    handle = LangfuseTraceHandle(run_context=run_context, started_at=time.perf_counter())

    client = _get_langfuse_client()
    if client is None:
        return handle

    try:
        handle.trace = client.trace(
            name=f"{run_context.feature}.{run_context.operation}",
            user_id=run_context.user_id,
            session_id=run_context.session_id,
            metadata=redact(run_context.metadata()),
            tags=tags or [],
        )
    except Exception as exc:
        logger.debug("Langfuse start_trace fallback (no explicit trace): %s", exc)
        handle.trace = None

    return handle


def end_trace(handle: LangfuseTraceHandle, success: bool, error: str | None = None) -> None:
    duration_ms = (time.perf_counter() - handle.started_at) * 1000.0
    trace_obj = handle.trace

    if trace_obj is not None:
        try:
            if hasattr(trace_obj, "update"):
                trace_obj.update(
                    metadata=redact(
                        {
                            **handle.run_context.metadata(),
                            "duration_ms": duration_ms,
                            "success": success,
                            "error": error,
                        }
                    )
                )
        except Exception as exc:
            logger.debug("Langfuse end_trace update failed: %s", exc)

    client = _get_langfuse_client()
    if client is not None:
        try:
            if hasattr(client, "flush"):
                client.flush()
        except Exception:
            pass
