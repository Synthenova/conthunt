"""Streak-related database queries (multi-type + daily ledger)."""
from uuid import UUID
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


def get_user_today(timezone: str) -> date:
    """Get current date in user's timezone."""
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


async def get_user_timezone(conn: AsyncConnection, user_id: UUID) -> str:
    """Get user's timezone from users table (source of truth)."""
    result = await conn.execute(
        text("SELECT timezone FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    return row[0] if row and row[0] else "UTC"


async def set_user_timezone(conn: AsyncConnection, user_id: UUID, timezone: str) -> None:
    """Persist user's timezone on session start/app open."""
    await conn.execute(
        text("""
        UPDATE users
        SET timezone = :timezone
        WHERE id = :user_id
        """),
        {"user_id": user_id, "timezone": timezone},
    )


async def get_streak_type_id(conn: AsyncConnection, streak_type: str) -> UUID:
    """Resolve streak type slug to ID."""
    result = await conn.execute(
        text("SELECT id FROM streak_types WHERE slug = :slug"),
        {"slug": streak_type},
    )
    row = result.fetchone()
    if not row:
        raise ValueError(f"Unknown streak type: {streak_type}")
    return row[0]


async def _get_user_streak_by_type_id(
    conn: AsyncConnection, user_id: UUID, streak_type_id: UUID
) -> dict | None:
    result = await conn.execute(
        text("""
        SELECT id, current_streak, longest_streak, last_activity_date, last_action_at
        FROM user_streaks
        WHERE user_id = :user_id AND streak_type_id = :streak_type_id
        """),
        {"user_id": user_id, "streak_type_id": streak_type_id},
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "current_streak": row[1],
        "longest_streak": row[2],
        "last_activity_date": row[3],
        "last_action_at": row[4],
    }


async def get_user_streak(conn: AsyncConnection, user_id: UUID, streak_type: str) -> dict | None:
    """Get user's streak data for a specific type."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    return await _get_user_streak_by_type_id(conn, user_id, streak_type_id)


async def _ensure_user_streak_by_type_id(
    conn: AsyncConnection, user_id: UUID, streak_type_id: UUID
) -> dict:
    await conn.execute(
        text("""
        INSERT INTO user_streaks (user_id, streak_type_id)
        VALUES (:user_id, :streak_type_id)
        ON CONFLICT (user_id, streak_type_id) DO NOTHING
        """),
        {"user_id": user_id, "streak_type_id": streak_type_id},
    )
    return await _get_user_streak_by_type_id(conn, user_id, streak_type_id)


async def ensure_user_streak(conn: AsyncConnection, user_id: UUID, streak_type: str) -> dict:
    """Ensure a streak record exists for the user + type."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    return await _ensure_user_streak_by_type_id(conn, user_id, streak_type_id)


async def reset_streak_if_missed(
    conn: AsyncConnection,
    user_id: UUID,
    streak_type: str,
    user_today: date,
) -> dict:
    """Reset streak if user missed more than one day."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    streak = await _get_user_streak_by_type_id(conn, user_id, streak_type_id)
    if not streak or not streak["last_activity_date"]:
        return streak

    days_since = (user_today - streak["last_activity_date"]).days
    if days_since > 1 and streak["current_streak"] != 0:
        await conn.execute(
            text("""
            UPDATE user_streaks
            SET current_streak = 0,
                updated_at = NOW()
            WHERE user_id = :user_id AND streak_type_id = :streak_type_id
            """),
            {"user_id": user_id, "streak_type_id": streak_type_id},
        )
        return await _get_user_streak_by_type_id(conn, user_id, streak_type_id)

    return streak


async def record_activity(
    conn: AsyncConnection,
    user_id: UUID,
    streak_type: str,
    timezone: str | None = None,
) -> dict:
    """Record activity and update streak if this is the first activity today."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    if timezone is None:
        timezone = await get_user_timezone(conn, user_id)
    user_today = get_user_today(timezone)

    await _ensure_user_streak_by_type_id(conn, user_id, streak_type_id)

    insert_result = await conn.execute(
        text("""
        INSERT INTO user_streak_days (user_id, streak_type_id, activity_date)
        VALUES (:user_id, :streak_type_id, :activity_date)
        ON CONFLICT (user_id, streak_type_id, activity_date) DO NOTHING
        RETURNING id
        """),
        {
            "user_id": user_id,
            "streak_type_id": streak_type_id,
            "activity_date": user_today,
        },
    )
    inserted = insert_result.fetchone() is not None

    if inserted:
        streak = await _get_user_streak_by_type_id(conn, user_id, streak_type_id)
        last_activity = streak["last_activity_date"]
        current = streak["current_streak"]
        if last_activity and (user_today - last_activity).days > 1:
            current = 0

        new_current = current + 1
        await conn.execute(
            text("""
            UPDATE user_streaks
            SET current_streak = :current_streak,
                longest_streak = GREATEST(longest_streak, :current_streak),
                last_activity_date = :activity_date,
                last_action_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id AND streak_type_id = :streak_type_id
            """),
            {
                "current_streak": new_current,
                "activity_date": user_today,
                "user_id": user_id,
                "streak_type_id": streak_type_id,
            },
        )
    else:
        await conn.execute(
            text("""
            UPDATE user_streaks
            SET last_action_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id AND streak_type_id = :streak_type_id
            """),
            {"user_id": user_id, "streak_type_id": streak_type_id},
        )

    return await _get_user_streak_by_type_id(conn, user_id, streak_type_id)


async def get_today_status(
    conn: AsyncConnection,
    user_id: UUID,
    streak_type: str,
    user_today: date,
) -> bool:
    """Check if user has completed today's activity for the type."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    result = await conn.execute(
        text("""
        SELECT 1
        FROM user_streak_days
        WHERE user_id = :user_id
          AND streak_type_id = :streak_type_id
          AND activity_date = :activity_date
        LIMIT 1
        """),
        {
            "user_id": user_id,
            "streak_type_id": streak_type_id,
            "activity_date": user_today,
        },
    )
    return result.fetchone() is not None


async def get_milestones(
    conn: AsyncConnection, role: str, streak_type: str
) -> list[dict]:
    """Get milestones for a role + type ordered by days required."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    result = await conn.execute(
        text("""
        SELECT
            days_required,
            reward_description,
            icon_name,
            reward_feature,
            reward_credits,
            reward_feature_amount
        FROM streak_milestones
        WHERE role = :role AND streak_type_id = :streak_type_id
        ORDER BY days_required ASC
        """),
        {"role": role, "streak_type_id": streak_type_id},
    )
    rows = result.fetchall()
    return [
        {
            "days_required": row[0],
            "reward_description": row[1],
            "icon_name": row[2],
            "reward_feature": row[3],
            "reward_credits": row[4],
            "reward_feature_amount": row[5],
        }
        for row in rows
    ]


async def get_claimed_days(
    conn: AsyncConnection,
    user_id: UUID,
    role: str,
    streak_type: str,
) -> set[int]:
    """Get days_required values already claimed for this role + type."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    result = await conn.execute(
        text("""
        SELECT days_required
        FROM streak_reward_grants
        WHERE user_id = :user_id AND role = :role AND streak_type_id = :streak_type_id
        """),
        {"user_id": user_id, "role": role, "streak_type_id": streak_type_id},
    )
    return {row[0] for row in result.fetchall()}


async def get_milestone_for_claim(
    conn: AsyncConnection,
    role: str,
    streak_type: str,
    days_required: int,
) -> dict | None:
    """Fetch a single milestone for claim validation."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    result = await conn.execute(
        text("""
        SELECT
            days_required,
            reward_description,
            icon_name,
            reward_feature,
            reward_credits,
            reward_feature_amount
        FROM streak_milestones
        WHERE role = :role AND streak_type_id = :streak_type_id AND days_required = :days_required
        """),
        {
            "role": role,
            "streak_type_id": streak_type_id,
            "days_required": days_required,
        },
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "days_required": row[0],
        "reward_description": row[1],
        "icon_name": row[2],
        "reward_feature": row[3],
        "reward_credits": row[4],
        "reward_feature_amount": row[5],
    }


async def get_reward_balance(
    conn: AsyncConnection,
    user_id: UUID,
    reward_feature: str | None,
) -> int:
    """Get reward balance for a user and type."""
    if reward_feature is None:
        result = await conn.execute(
            text("""
            SELECT balance
            FROM reward_balances
            WHERE user_id = :user_id AND reward_feature IS NULL
            """),
            {"user_id": user_id},
        )
    else:
        result = await conn.execute(
            text("""
            SELECT balance
            FROM reward_balances
            WHERE user_id = :user_id AND reward_feature = :reward_feature
            """),
            {"user_id": user_id, "reward_feature": reward_feature},
        )
    row = result.fetchone()
    return row[0] if row and row[0] is not None else 0


async def grant_reward(
    conn: AsyncConnection,
    user_id: UUID,
    role: str,
    streak_type: str,
    milestone: dict,
) -> dict | None:
    """Grant a reward for a milestone if not already claimed."""
    streak_type_id = await get_streak_type_id(conn, streak_type)
    result = await conn.execute(
        text("""
        INSERT INTO streak_reward_grants (
            user_id,
            streak_type_id,
            days_required,
            role,
            reward_feature,
            reward_credits,
            reward_feature_amount
        )
        VALUES (
            :user_id,
            :streak_type_id,
            :days_required,
            :role,
            :reward_feature,
            :reward_credits,
            :reward_feature_amount
        )
        ON CONFLICT (user_id, streak_type_id, days_required, role) DO NOTHING
        RETURNING id
        """),
        {
            "user_id": user_id,
            "streak_type_id": streak_type_id,
            "days_required": milestone["days_required"],
            "role": role,
            "reward_feature": milestone["reward_feature"],
            "reward_credits": milestone["reward_credits"],
            "reward_feature_amount": milestone["reward_feature_amount"],
        },
    )
    inserted = result.fetchone() is not None
    if not inserted:
        return None

    if milestone["reward_credits"] > 0:
        await conn.execute(
            text("""
            INSERT INTO reward_balances (user_id, reward_feature, balance, updated_at)
            VALUES (:user_id, NULL, :reward_credits, NOW())
            ON CONFLICT (user_id) WHERE reward_feature IS NULL DO UPDATE
            SET balance = reward_balances.balance + EXCLUDED.balance,
                updated_at = NOW()
            """),
            {
                "user_id": user_id,
                "reward_credits": milestone["reward_credits"],
            },
        )

    if milestone["reward_feature"] and milestone["reward_feature_amount"] > 0:
        await conn.execute(
            text("""
            INSERT INTO reward_balances (user_id, reward_feature, balance, updated_at)
            VALUES (:user_id, :reward_feature, :reward_feature_amount, NOW())
            ON CONFLICT (user_id, reward_feature) DO UPDATE
            SET balance = reward_balances.balance + EXCLUDED.balance,
                updated_at = NOW()
            """),
            {
                "user_id": user_id,
                "reward_feature": milestone["reward_feature"],
                "reward_feature_amount": milestone["reward_feature_amount"],
            },
        )

    new_credits_balance = await get_reward_balance(conn, user_id, None)
    new_feature_balance = (
        await get_reward_balance(conn, user_id, milestone["reward_feature"])
        if milestone["reward_feature"]
        else 0
    )
    return {
        "credits_balance": new_credits_balance,
        "feature_balance": new_feature_balance,
    }


async def get_next_milestone(current_streak: int, milestones: list[dict]) -> dict | None:
    """Get the next milestone to achieve."""
    for milestone in milestones:
        if milestone["days_required"] > current_streak:
            return milestone
    return None
