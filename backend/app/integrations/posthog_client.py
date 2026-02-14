from __future__ import annotations

from typing import Any

from app.core import get_settings, logger

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

        if hasattr(client, "capture"):
            try:
                client.capture(
                    distinct_id=distinct_id,
                    event=event,
                    properties=properties or {},
                )
            except TypeError:
                client.capture(distinct_id, event, properties or {})
        else:
            return False
        return True
    except Exception as exc:
        logger.warning("PostHog capture failed for event=%s: %s", event, exc)
        return False
