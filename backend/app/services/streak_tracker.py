"""Centralized streak activity recorder with telemetry/logging."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import logger
from app.db.queries import streaks as streak_queries
from app.integrations.posthog_client import capture_event


async def record_streak_activity_once_per_day(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    streak_type: str,
    timezone: str,
    source: str,
) -> dict:
    """
    Record daily streak activity for a user/type.

    Uses DB-level uniqueness for once-per-day behavior and emits
    lightweight telemetry/logs for observability.
    """
    activity_date = streak_queries.get_user_today(timezone).isoformat()
    distinct_id = str(user_id)
    properties = {
        "streak_type": streak_type,
        "source": source,
        "activity_date": activity_date,
        "attempted": True,
    }

    logger.info(
        "[STREAK] attempt user_id=%s streak_type=%s source=%s activity_date=%s",
        distinct_id,
        streak_type,
        source,
        activity_date,
    )
    capture_event(
        distinct_id=distinct_id,
        event="streak_attempt_total",
        properties=properties,
    )

    streak = await streak_queries.record_activity(
        conn,
        user_id,
        streak_type,
        timezone=timezone,
    )
    inserted_today = bool(streak.get("inserted_today"))
    outcome_event = "streak_inserted_total" if inserted_today else "streak_same_day_noop_total"

    logger.info(
        "[STREAK] outcome user_id=%s streak_type=%s source=%s activity_date=%s inserted_today=%s current_streak=%s",
        distinct_id,
        streak_type,
        source,
        activity_date,
        inserted_today,
        streak.get("current_streak"),
    )
    capture_event(
        distinct_id=distinct_id,
        event=outcome_event,
        properties={
            **properties,
            "inserted_today": inserted_today,
            "current_streak": streak.get("current_streak"),
        },
    )
    return streak
