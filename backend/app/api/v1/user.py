"""User profile endpoint."""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.auth import get_current_user, AuthUser
from app.core import logger
from app.db.session import get_db_connection
from app.services.credit_tracker import credit_tracker

router = APIRouter(prefix="/user", tags=["user"])


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
