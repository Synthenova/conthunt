"""Firebase authentication module."""
import os
from typing import Optional
from typing_extensions import TypedDict

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Header, HTTPException

_app = None


class AuthUser(TypedDict):
    """Authenticated user context."""
    uid: str               # Firebase UID
    email: Optional[str]   # From Firebase token
    role: str              # From custom claims (defaults to 'free')


def init_firebase():
    global _app
    if _app:
        return _app

    # Option A: ADC via GOOGLE_APPLICATION_CREDENTIALS or runtime credentials
    # Option B: explicit service account json path (also via GOOGLE_APPLICATION_CREDENTIALS)
    try:
        _app = firebase_admin.initialize_app(options={
            "projectId": os.getenv("GCLOUD_PROJECT", "conthunt-dev")
        })
    except ValueError:
        # already initialized
        _app = firebase_admin.get_app()
    return _app


init_firebase()


def get_current_user(authorization: str = Header(default="")) -> AuthUser:
    """
    Extract and verify Firebase ID token from Authorization header.
    
    Returns AuthUser with role from custom claims (defaults to 'free').
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    id_token = authorization.split(" ", 1)[1].strip()

    try:
        decoded = auth.verify_id_token(id_token)
        return AuthUser(
            uid=decoded.get("uid"),
            email=decoded.get("email"),
            role=decoded.get("role", "free"),  # Custom claim, defaults to 'free'
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

