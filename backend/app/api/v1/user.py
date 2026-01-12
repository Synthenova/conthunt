"""User profile endpoint."""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.auth import get_current_user, AuthUser
from app.db.session import get_db_connection
from app.services.credit_tracker import credit_tracker

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    """
    Returns the current user's profile information and usage statistics.
    Formats usage data for frontend compatibility.
    """
    user_uuid = user["db_user_id"]  # Already a UUID
    firebase_uid = user["uid"]
    role = user["role"]
    
    # Get period_start from DB
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT current_period_start FROM users WHERE id = :id"),
            {"id": user_uuid}
        )
        row = result.fetchone()
        period_start = row[0] if row else None
    
    # Get credit-based summary
    summary = await credit_tracker.get_usage_summary(user_uuid, role, period_start)
    
    # Transform to frontend expected format: [{feature, period, limit, used}]
    usage_list = []
    
    # Add total credits as a "feature"
    usage_list.append({
        "feature": "credits",
        "period": "monthly",
        "limit": summary["credits"]["total"],
        "used": summary["credits"]["used"]
    })
    
    # Add each capped feature
    # Add each feature (even if uncapped)
    for feature, data in summary["features"].items():
        usage_list.append({
            "feature": feature,
            "period": "monthly",
            "limit": data["cap"],  # None for unlimited
            "used": data["uses"]
        })
    
    return {
        "id": str(user_uuid),
        "firebase_uid": firebase_uid,
        "email": user.get("email"),
        "role": role,
        "usage": usage_list
    }
