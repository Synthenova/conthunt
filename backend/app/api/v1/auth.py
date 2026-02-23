"""Auth sync endpoint - creates user and sets Firebase claims."""
from fastapi import APIRouter, Header, HTTPException
from firebase_admin import auth

from app.db import get_or_create_user
from app.db.session import get_db_connection
from app.integrations.posthog_client import capture_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sync")
async def sync_user(authorization: str = Header(default="")):
    """
    Sync user with backend after Firebase login.
    
    This endpoint:
    1. Verifies the Firebase ID token
    2. Creates user in DB if not exists
    3. Sets custom claims (db_user_id, role) on Firebase
    4. Returns success + flag to refresh token
    
    Frontend MUST call this after successful Firebase login,
    then call getIdToken(true) to get fresh token with claims.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    
    id_token = authorization.split(" ", 1)[1].strip()
    
    try:
        # Verify the token (doesn't require db_user_id yet)
        decoded = auth.verify_id_token(id_token)
        firebase_uid = decoded.get("uid")
        
        if not firebase_uid:
            raise HTTPException(status_code=401, detail="Invalid token: no uid")
        
        # Create user in DB if needed and set claims
        async with get_db_connection() as conn:
            user_uuid, role, claims_set = await get_or_create_user(
                conn,
                firebase_uid,
                sync_claims=True  # This sets db_user_id and role on Firebase
            )
            await conn.commit()

        # Track signup for new users (role="free" means new user creation)
        if role == "free" and claims_set:
            capture_event(
                distinct_id=str(user_uuid),
                event="user_signup",
                properties={
                    "role": role,
                    "provider": "firebase",
                    "email": decoded.get("email"),
                },
            )
        # Track user login (both new and existing users)
        capture_event(
            distinct_id=str(user_uuid),
            event="user_login",
            properties={
                "role": role,
                "provider": "firebase",
                "email": decoded.get("email"),
            },
        )
        
        return {
            "success": True,
            "user_id": str(user_uuid),
            "role": role,
            "needs_token_refresh": claims_set,  # FE should call getIdToken(true)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")
