from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEYWORDS = (
    "token",
    "secret",
    "password",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "webhook_signature",
)

_BEARER_RE = re.compile(r"^Bearer\s+.+", re.IGNORECASE)


def _looks_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def _redact_string(value: str) -> str:
    if _BEARER_RE.match(value):
        return REDACTED
    if len(value) > 80 and any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
        return REDACTED
    return value


def redact(payload: Any) -> Any:
    if payload is None:
        return None

    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if _looks_sensitive_key(str(key)):
                sanitized[str(key)] = REDACTED
            else:
                sanitized[str(key)] = redact(value)
        return sanitized

    if isinstance(payload, list):
        return [redact(item) for item in payload]

    if isinstance(payload, tuple):
        return tuple(redact(item) for item in payload)

    if isinstance(payload, str):
        return _redact_string(payload)

    return payload
