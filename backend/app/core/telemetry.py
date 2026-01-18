"""OpenTelemetry tracing setup."""
from __future__ import annotations

import asyncio
import os
from functools import wraps
from typing import Any, Callable

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.settings import get_settings

_telemetry_initialized = False


def _parse_resource_attributes(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    attrs: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            attrs[key] = value
    return attrs


def _build_resource() -> Resource:
    settings = get_settings()
    raw_attrs = settings.OTEL_RESOURCE_ATTRIBUTES
    service_name = settings.OTEL_SERVICE_NAME
    print(raw_attrs, service_name)
    attrs = _parse_resource_attributes(raw_attrs)
    if service_name:
        attrs.setdefault(SERVICE_NAME, service_name)
    return Resource.create(attrs)


def setup_telemetry(app: Any | None = None) -> None:
    """Initialize tracing and instrument libraries."""
    global _telemetry_initialized
    if _telemetry_initialized:
        return

    provider = TracerProvider(resource=_build_resource())
    provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
    trace.set_tracer_provider(provider)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    try:
        from app.db import engine

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except Exception as e:
        logger.warning("SQLAlchemy instrumentation skipped: %s", e)

    HTTPXClientInstrumentor().instrument()
    _telemetry_initialized = True


def trace_span(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to wrap a function in a span."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        span_name = name or func.__qualname__
        tracer = trace.get_tracer(func.__module__)

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name):
                    return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator
