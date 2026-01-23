"""User profile endpoint."""
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from app.auth import get_current_user, AuthUser
from app.core import logger
from app.db.session import get_db_connection
from app.services.credit_tracker import credit_tracker

router = APIRouter(prefix="/user", tags=["user"])


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _add_months(value: date, delta: int) -> date:
    month = value.month + delta
    year = value.year
    while month > 12:
        month -= 12
        year += 1
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    """
    Returns the current user's profile information and usage statistics.
    Includes credits summary and next reset date.
    
    Also ensures Firebase claims are in sync with DB role (self-healing).
    """
    user_uuid = user["db_user_id"]
    firebase_uid = user["uid"]
    token_role = user["role"]
    
    # Get DB role and period_start
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT role, current_period_start FROM users WHERE id = :id"),
            {"id": user_uuid}
        )
        row = result.fetchone()
        db_role = row[0] if row else "free"
        period_start = row[1] if row else None
    
    # Self-healing: if DB role differs from token role, sync Firebase claims
    if db_role != token_role:
        logger.info(f"Role mismatch for user {user_uuid}: token={token_role}, db={db_role}. Syncing...")
        try:
            from firebase_admin import auth
            fb_user = auth.get_user(firebase_uid)
            claims = fb_user.custom_claims or {}
            claims["role"] = db_role
            auth.set_custom_user_claims(firebase_uid, claims)
            logger.info(f"Synced Firebase claims for user {user_uuid}: role={db_role}")
        except Exception as e:
            logger.error(f"Failed to sync Firebase claims for user {user_uuid}: {e}")
    
    # Use DB role as source of truth
    role = db_role
    
    # Get credit-based summary (includes automatic period advancement)
    summary = await credit_tracker.get_usage_summary(user_uuid, role, period_start)
    logger.info(f"Usage summary for user {user_uuid}: {summary}")
    # Transform to frontend expected format
    usage_list = []
    for feature, data in summary["features"].items():
        usage_list.append({
            "feature": feature,
            "period": "monthly",
            "limit": data["cap"],
            "used": data["uses"]
        })
    
    return {
        "id": str(user_uuid),
        "firebase_uid": firebase_uid,
        "email": user.get("email"),
        "role": role,
        "usage": usage_list,
        "credits": summary["credits"],
        "reward_balances": summary.get("reward_balances", {}),
        "period_start": summary["period_start"],
        "next_reset": summary.get("next_reset"),
    }


@router.get("/usage-series")
async def get_usage_series(
    user: AuthUser = Depends(get_current_user),
    range: str = Query(default="daily", pattern="^(daily|monthly)$"),
    limit: int = Query(default=7, ge=2, le=365),
):
    """Return per-period search uses and credits used for charting."""
    user_uuid = user["db_user_id"]
    today = datetime.utcnow().date()

    if range == "monthly":
        end_date = _month_start(today)
        start_date = _add_months(end_date, -(limit - 1))
        end_exclusive = _add_months(end_date, 1)
        step = "1 month"
        trunc = "month"
    else:
        end_date = today
        start_date = today - timedelta(days=limit - 1)
        end_exclusive = end_date + timedelta(days=1)
        step = "1 day"
        trunc = "day"

    async with get_db_connection() as conn:
        result = await conn.execute(
            text(
                f"""
                WITH buckets AS (
                    SELECT generate_series(
                        CAST(:start_date AS date),
                        CAST(:end_date AS date),
                        interval '{step}'
                    ) AS bucket
                ),
                usage AS (
                    SELECT date_trunc('{trunc}', created_at) AS bucket,
                           COUNT(*) FILTER (WHERE feature = 'search_query') AS searches,
                           COALESCE(SUM(quantity), 0) AS credits
                    FROM usage_logs
                    WHERE user_id = :user_id
                      AND created_at >= :start_ts
                      AND created_at < :end_exclusive
                    GROUP BY 1
                )
                SELECT
                    buckets.bucket::date AS bucket,
                    COALESCE(usage.searches, 0) AS searches,
                    COALESCE(usage.credits, 0) AS credits
                FROM buckets
                LEFT JOIN usage ON usage.bucket = buckets.bucket
                ORDER BY buckets.bucket
                """
            ),
            {
                "user_id": user_uuid,
                "start_date": start_date,
                "end_date": end_date,
                "start_ts": start_date,
                "end_exclusive": end_exclusive,
            },
        )

    series = [
        {
            "date": row[0].isoformat(),
            "searches": row[1],
            "credits": row[2],
        }
        for row in result.fetchall()
    ]
    return {"range": range, "series": series}
