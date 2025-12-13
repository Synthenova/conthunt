"""User management - Firebase UID to internal UUID mapping."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_or_create_user(conn: AsyncConnection, firebase_uid: str) -> UUID:
    """
    Get or create internal user record from Firebase UID.
    
    Uses INSERT ... ON CONFLICT to atomically get or create the user,
    returning the internal UUID.
    """
    result = await conn.execute(
        text("""
            INSERT INTO users (firebase_uid)
            VALUES (:firebase_uid)
            ON CONFLICT (firebase_uid) 
            DO UPDATE SET firebase_uid = EXCLUDED.firebase_uid
            RETURNING id
        """),
        {"firebase_uid": firebase_uid}
    )
    row = result.fetchone()
    return row[0]
