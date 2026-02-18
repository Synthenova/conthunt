"""Firebase authentication module."""
import os
import asyncio
from typing import Optional
from typing_extensions import TypedDict
from uuid import UUID
from app.core.settings import get_settings


import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Cookie, Header, HTTPException, Request
from opentelemetry import trace

from app.core.telemetry_context import update_request_telemetry

_app = None

app_settings = get_settings()

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
        # Check for explicit credentials path (Local Dev)
        cred_path = app_settings.GOOGLE_APPLICATION_CREDENTIALS_FB
        cred = None
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        
        _app = firebase_admin.initialize_app(credential=cred, options={
            "projectId": app_settings.GCLOUD_PROJECT
        })
    except ValueError:
        try:
            _app = firebase_admin.get_app()
        except ValueError:
            _app = firebase_admin.initialize_app()
    return _app

# Initialize on module load
init_firebase()


async def get_current_user(
    request: Request,
    authorization: str = Header(default=""),
    session: str | None = Cookie(default=None),
) -> AuthUser:
    """
    Extract and verify Firebase auth from either:
    - Authorization: Bearer <ID_TOKEN> (API clients)
    - Cookie: session=<SESSION_COOKIE> (browser media loads, Next.js rewrites/proxy)
    
    REQUIRES db_user_id in JWT custom claims. If missing, returns 401.
    Existing users without claims must log out and log back in.
    """
    try:
        decoded = None

        if authorization.startswith("Bearer "):
            id_token = authorization.split(" ", 1)[1].strip()
            # firebase_admin verification is blocking; run in a thread so we don't block the event loop.
            decoded = await asyncio.to_thread(auth.verify_id_token, id_token)
        elif session:
            # Browser requests (img/video tags) can't attach Authorization headers. We support
            # Firebase session cookies so these requests can still be authenticated.
            decoded = await asyncio.to_thread(auth.verify_session_cookie, session, True)
        else:
            raise HTTPException(status_code=401, detail="Missing credentials")

        db_user_id_str = decoded.get("db_user_id")
        
        # REQUIRE db_user_id - if missing, user needs to re-login
        if not db_user_id_str:
            raise HTTPException(
                status_code=401, 
                detail="Session expired. Please log out and log back in."
            )

        auth_user = AuthUser(
            uid=decoded.get("uid"),
            db_user_id=UUID(db_user_id_str),
            email=decoded.get("email"),
            role=decoded.get("role", "free"),
        )

        user_id = str(auth_user["db_user_id"])
        update_request_telemetry(request, user_id=user_id)

        span = trace.get_current_span()
        if span is not None:
            span.set_attribute("enduser.id", user_id)

        return auth_user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
