from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.auth import get_current_user, AuthUser
from app.db.session import get_db_connection
from app.services.usage_tracker import usage_tracker

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    """
    Returns the current user's profile information and usage statistics.
    """
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT id, firebase_uid, role FROM users WHERE firebase_uid = :uid"),
            {"uid": user["uid"]}
        )
        row = result.fetchone()
        
        # We always return the role from user object (custom claims) 
        # as the source of truth for the session, but we use DB for tracking.
        firebase_uid = user["uid"]
        role = user["role"]
        
        usage = await usage_tracker.get_usage_summary(firebase_uid, role)
        
        return {
            "id": str(row[0]) if row else None,
            "firebase_uid": firebase_uid,
            "email": user.get("email"),
            "role": role,
            "usage": usage
        }
