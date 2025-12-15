"""User management - Firebase UID to internal UUID mapping."""
from uuid import UUID
from typing import Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_or_create_user(conn: AsyncConnection, firebase_uid: str) -> Tuple[UUID, str]:
    """
    Get or create internal user record from Firebase UID.
    
    Uses INSERT ... ON CONFLICT to atomically get or create the user,
    returning the internal UUID and role.
    """
    result = await conn.execute(
        text("""
            INSERT INTO users (firebase_uid, role)
            VALUES (:firebase_uid, 'free')
            ON CONFLICT (firebase_uid) 
            DO UPDATE SET firebase_uid = EXCLUDED.firebase_uid
            RETURNING id, role
        """),
        {"firebase_uid": firebase_uid}
    )
    row = result.fetchone()
    return row[0], row[1]

