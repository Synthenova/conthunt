"""Firebase authentication module."""
import os
from typing import Optional
from typing_extensions import TypedDict
from uuid import UUID

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Header, HTTPException, Depends

_app = None


class AuthUser(TypedDict):
    """Authenticated user context."""
    uid: str                        # Firebase UID
    db_user_id: UUID                # Internal DB UUID (from custom claim) - REQUIRED
    email: Optional[str]            # From Firebase token
    role: str                       # From custom claims (defaults to 'free')


def init_firebase():
    global _app
    if _app:
        return _app

    try:
        _app = firebase_admin.initialize_app(options={
            "projectId": os.getenv("GCLOUD_PROJECT", "conthunt-dev")
        })
    except ValueError:
        _app = firebase_admin.get_app()
    return _app


init_firebase()


def get_current_user(authorization: str = Header(default="")) -> AuthUser:
    """
    Extract and verify Firebase ID token from Authorization header.
    
    REQUIRES db_user_id in JWT custom claims. If missing, returns 401.
    Existing users without claims must log out and log back in.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    id_token = authorization.split(" ", 1)[1].strip()

    try:
        decoded = auth.verify_id_token(id_token)
        db_user_id_str = decoded.get("db_user_id")
        
        # REQUIRE db_user_id - if missing, user needs to re-login
        if not db_user_id_str:
            raise HTTPException(
                status_code=401, 
                detail="Session expired. Please log out and log back in."
            )
        
        return AuthUser(
            uid=decoded.get("uid"),
            db_user_id=UUID(db_user_id_str),
            email=decoded.get("email"),
            role=decoded.get("role", "free"),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
