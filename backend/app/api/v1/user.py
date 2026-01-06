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
    # db_user_id is guaranteed from JWT (get_current_user returns 401 if missing)
    user_uuid = user["db_user_id"]
    firebase_uid = user["uid"]
    role = user["role"]
    
    usage = await usage_tracker.get_usage_summary(user_uuid, role)
    
    return {
        "id": str(user_uuid),
        "firebase_uid": firebase_uid,
        "email": user.get("email"),
        "role": role,
        "usage": usage
    }
