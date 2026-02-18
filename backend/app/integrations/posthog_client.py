from __future__ import annotations

from typing import Any

from app.core import get_settings, logger


# Error categorization for better PostHog analytics
ERROR_CATEGORIES: dict[str, str] = {
    # Timeout errors
    "Timeout": "timeout",
    "TimeoutError": "timeout",
    "asyncio.TimeoutError": "timeout",

    # HTTP errors
    "HTTPStatusError": "http_error",
    "HTTPError": "http_error",

    # Network errors
    "ConnectError": "network_error",
    "NetworkError": "network_error",
    "ConnectionError": "network_error",

    # Validation errors
    "ValueError": "validation_error",
    "TypeError": "validation_error",
    "KeyError": "validation_error",
    "ValidationError": "validation_error",

    # Database errors
    "OperationalError": "database_error",
    "DatabaseError": "database_error",

    # Rate limiting
    "LlmRateLimited": "rate_limit",

    # Platform-specific errors
    "JSONDecodeError": "parsing_error",

    # Unknown/fallback
    "Exception": "unknown_error",
}


def categorize_error(exception: Exception | None) -> str:
    """
    Categorize an exception for PostHog tracking.
    Returns a high-level category like 'timeout', 'http_error', etc.
    """
    if exception is None:
        return "unknown_error"

    exception_name = type(exception).__name__
    return ERROR_CATEGORIES.get(exception_name, "unknown_error")

try:
    import posthog  # type: ignore
except Exception:  # pragma: no cover
    posthog = None


_configured = False
_posthog_client: Any | None = None


def _configure() -> bool:
    global _configured, _posthog_client
    if _configured:
        return True

    settings = get_settings()
    if not getattr(settings, "TELEMETRY_POSTHOG_ENABLED", True):
        return False
    if not settings.POSTHOG_PROJECT_API_KEY:
        return False
    if posthog is None:
        logger.warning("PostHog SDK unavailable; server analytics disabled")
        return False

    host = settings.POSTHOG_HOST or "https://app.posthog.com"
    try:
        if hasattr(posthog, "Posthog"):
            _posthog_client = posthog.Posthog(settings.POSTHOG_PROJECT_API_KEY, host=host)
        else:
            posthog.project_api_key = settings.POSTHOG_PROJECT_API_KEY
            posthog.host = host
            _posthog_client = posthog
    except Exception as exc:
        logger.warning("PostHog init failed: %s", exc)
        _posthog_client = None
        return False

    _configured = True
    return True


def capture_event_with_error(
    *,
    distinct_id: str,
    event: str,
    properties: dict[str, Any] | None = None,
    exception: Exception | None = None,
) -> bool:
    """
    Capture an event and automatically categorize any exception.
    Adds error_category and error_type properties if exception is provided.
    """
    if exception is not None:
        if properties is None:
            properties = {}
        properties = dict(properties)  # Make a copy
        properties["error_category"] = categorize_error(exception)
        properties["error_type"] = type(exception).__name__

    return capture_event(
        distinct_id=distinct_id,
        event=event,
        properties=properties,
    )


def capture_event(
    *,
    distinct_id: str,
    event: str,
    properties: dict[str, Any] | None = None,
) -> bool:
    if not distinct_id or not event:
        return False

    if not _configure():
        return False

    try:
        client = _posthog_client or posthog
        if client is None:
            return False

        event_properties = dict(properties or {})
        event_properties.setdefault("source", "backend_api")

        if hasattr(client, "capture"):
            try:
                client.capture(
                    distinct_id=distinct_id,
                    event=event,
                    properties=event_properties,
                )
            except TypeError:
                client.capture(distinct_id, event, event_properties)
        else:
            return False
        return True
    except Exception as exc:
        logger.warning("PostHog capture failed for event=%s: %s", event, exc)
        return False
