"""User management - Firebase UID to internal UUID mapping."""
from uuid import UUID
from typing import Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing
from app.core import logger


@log_query_timing
async def get_or_create_user(
    conn: AsyncConnection, 
    firebase_uid: str,
    sync_claims: bool = True
) -> Tuple[UUID, str, bool]:
    """
    Get or create internal user record from Firebase UID.
    
    Uses INSERT ... ON CONFLICT to atomically get or create the user.
    If sync_claims=True, ALWAYS sets Firebase custom claims (for new AND existing users).
    
    Returns: (uuid, role, claims_were_set)
    """
    # Upsert user - either get existing or create new
    result = await conn.execute(
        text("""
            INSERT INTO users (firebase_uid, role, current_period_start)
            VALUES (:firebase_uid, 'free', NOW())
            ON CONFLICT (firebase_uid) 
            DO UPDATE SET firebase_uid = EXCLUDED.firebase_uid
            RETURNING id, role
        """),
        {"firebase_uid": firebase_uid}
    )
    row = result.fetchone()
    user_uuid, role = row[0], row[1]
    await conn.commit()
    
    # ALWAYS set Firebase custom claims if sync_claims=True
    # This ensures existing users without claims also get them
    claims_set = False
    if sync_claims:
        try:
            from firebase_admin import auth
            auth.set_custom_user_claims(firebase_uid, {
                "db_user_id": str(user_uuid),
                "role": role
            })
            logger.info(f"Set Firebase claims for user {firebase_uid}: db_user_id={user_uuid}, role={role}")
            claims_set = True
        except Exception as e:
            logger.error(f"Failed to set Firebase claims for {firebase_uid}: {e}")
    
    return user_uuid, role, claims_set

