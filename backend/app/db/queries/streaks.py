"""Streak-related database queries."""
from uuid import UUID
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_user_streak(conn: AsyncConnection, user_id: UUID) -> dict | None:
    """Get user's current streak data."""
    result = await conn.execute(
        text("""
        SELECT id, current_streak, longest_streak, last_activity_date,
               last_search_at, last_app_open_at, timezone, created_at, updated_at
        FROM user_streaks WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "current_streak": row[1],
        "longest_streak": row[2],
        "last_activity_date": row[3],
        "last_search_at": row[4],
        "last_app_open_at": row[5],
        "timezone": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


async def get_milestones(conn: AsyncConnection) -> list[dict]:
    """Get all streak milestones ordered by days required."""
    result = await conn.execute(
        text("""
        SELECT days_required, reward_description, icon_name
        FROM streak_milestones
        ORDER BY days_required ASC
        """)
    )
    rows = result.fetchall()
    return [
        {
            "days_required": row[0],
            "reward_description": row[1],
            "icon_name": row[2],
        }
        for row in rows
    ]


async def ensure_streak_record(conn: AsyncConnection, user_id: UUID, timezone: str = "UTC") -> dict:
    """Ensure a streak record exists for the user, creating one if needed."""
    # Try to get existing record
    existing = await get_user_streak(conn, user_id)
    if existing:
        return existing
    
    # Create new record
    result = await conn.execute(
        text("""
        INSERT INTO user_streaks (user_id, timezone)
        VALUES (:user_id, :timezone)
        ON CONFLICT (user_id) DO UPDATE SET timezone = EXCLUDED.timezone
        RETURNING id, current_streak, longest_streak, last_activity_date,
                  last_search_at, last_app_open_at, timezone, created_at, updated_at
        """),
        {"user_id": user_id, "timezone": timezone}
    )
    await conn.commit()
    row = result.fetchone()
    return {
        "id": row[0],
        "current_streak": row[1],
        "longest_streak": row[2],
        "last_activity_date": row[3],
        "last_search_at": row[4],
        "last_app_open_at": row[5],
        "timezone": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


def get_user_today(timezone: str) -> date:
    """Get current date in user's timezone."""
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


async def record_app_open(conn: AsyncConnection, user_id: UUID, timezone: str = "UTC") -> dict:
    """Record app open event and potentially update streak."""
    streak = await ensure_streak_record(conn, user_id, timezone)
    user_today = get_user_today(timezone)
    
    # Update last_app_open_at and timezone
    await conn.execute(
        text("""
        UPDATE user_streaks
        SET last_app_open_at = NOW(),
            timezone = :timezone,
            updated_at = NOW()
        WHERE user_id = :user_id
        """),
        {"user_id": user_id, "timezone": timezone}
    )
    await conn.commit()
    
    # Check if streak needs reset (missed days)
    streak = await check_streak_reset(conn, user_id, user_today)
    
    return streak


async def record_search_activity(conn: AsyncConnection, user_id: UUID, timezone: str = "UTC") -> dict:
    """Record search activity and update streak if day is now complete."""
    streak = await ensure_streak_record(conn, user_id, timezone)
    user_today = get_user_today(timezone)
    
    # Check if streak needs reset first
    streak = await check_streak_reset(conn, user_id, user_today)
    
    # Update last_search_at
    await conn.execute(
        text("""
        UPDATE user_streaks
        SET last_search_at = NOW(),
            updated_at = NOW()
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    await conn.commit()
    
    # Refresh streak data
    streak = await get_user_streak(conn, user_id)
    
    # Check if both conditions are met for today
    if streak["last_app_open_at"] and streak["last_search_at"]:
        last_app_open_date = streak["last_app_open_at"].astimezone(ZoneInfo(timezone)).date() if streak["last_app_open_at"] else None
        last_search_date = streak["last_search_at"].astimezone(ZoneInfo(timezone)).date() if streak["last_search_at"] else None
        
        # Both actions happened today
        if last_app_open_date == user_today and last_search_date == user_today:
            # Check if we haven't already counted today
            if streak["last_activity_date"] != user_today:
                streak = await increment_streak(conn, user_id, user_today)
    
    return streak


async def check_streak_reset(conn: AsyncConnection, user_id: UUID, user_today: date) -> dict:
    """Check if streak should be reset due to missed days."""
    streak = await get_user_streak(conn, user_id)
    if not streak or not streak["last_activity_date"]:
        return streak
    
    last_activity = streak["last_activity_date"]
    days_since = (user_today - last_activity).days
    
    # If more than 1 day has passed, reset streak
    if days_since > 1:
        await conn.execute(
            text("""
            UPDATE user_streaks
            SET current_streak = 0,
                updated_at = NOW()
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        await conn.commit()
        streak = await get_user_streak(conn, user_id)
    
    return streak


async def increment_streak(conn: AsyncConnection, user_id: UUID, activity_date: date) -> dict:
    """Increment the streak and update last_activity_date."""
    await conn.execute(
        text("""
        UPDATE user_streaks
        SET current_streak = current_streak + 1,
            longest_streak = GREATEST(longest_streak, current_streak + 1),
            last_activity_date = :activity_date,
            updated_at = NOW()
        WHERE user_id = :user_id
        """),
        {"user_id": user_id, "activity_date": activity_date}
    )
    await conn.commit()
    return await get_user_streak(conn, user_id)


async def get_next_milestone(current_streak: int, milestones: list[dict]) -> dict | None:
    """Get the next milestone to achieve."""
    for milestone in milestones:
        if milestone["days_required"] > current_streak:
            return milestone
    return None
