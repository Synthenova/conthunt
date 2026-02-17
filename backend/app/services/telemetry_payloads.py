from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from app.platforms.base import PlatformCallResult


def _platform_error_category(result: PlatformCallResult) -> str | None:
    if result.success:
        return None
    if result.http_status:
        return "http_error"
    if result.error:
        return "platform_error"
    return "unknown_error"


def build_platform_result_props(
    *,
    search_id: UUID,
    result: PlatformCallResult,
    source: str,
) -> dict[str, Any]:
    return {
        "search_id": str(search_id),
        "platform": result.platform,
        "success": result.success,
        "duration_ms": result.duration_ms,
        "result_count": len(result.parsed.items) if result.parsed else 0,
        "http_status": result.http_status,
        "error_type": "PlatformCallError" if result.error else None,
        "error_category": _platform_error_category(result),
        "source": source,
    }


def build_search_completed_props(
    *,
    search_id: UUID,
    queue_duration_ms: int,
    start_time_s: float,
    platform_count: int,
    result_count_total: int,
    success: bool,
    source: str,
    error: str | None = None,
) -> dict[str, Any]:
    duration_ms = int((time.time() - start_time_s) * 1000)
    props: dict[str, Any] = {
        "search_id": str(search_id),
        "success": success,
        "duration_ms": duration_ms,
        "total_duration_ms": duration_ms + queue_duration_ms,
        "queue_duration_ms": queue_duration_ms,
        "platform_count": platform_count,
        "result_count_total": result_count_total,
        "source": source,
    }
    if error:
        props["error"] = error
    return props
