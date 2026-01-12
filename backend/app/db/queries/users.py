"""User-related database queries."""
from uuid import UUID
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing



async def get_user_id_by_firebase(conn: AsyncConnection, firebase_uid: str) -> UUID | None:
    """Get internal user ID from Firebase UID. Use this first in webhooks."""
    result = await conn.execute(
        text("SELECT id FROM users WHERE firebase_uid = :firebase_uid"),
        {"firebase_uid": firebase_uid}
    )
    row = result.fetchone()
    return row[0] if row else None



async def get_user_role(conn: AsyncConnection, user_id: UUID) -> str:
    """Get user's current role."""
    result = await conn.execute(
        text("SELECT role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    return row[0] if row else "free"



async def get_user_by_uuid(conn: AsyncConnection, user_id: UUID) -> dict | None:
    """Get user details by internal UUID."""
    result = await conn.execute(
        text("""
        SELECT id, firebase_uid, email, role, current_period_start 
        FROM users WHERE id = :user_id
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "firebase_uid": row[1],
        "email": row[2],
        "role": row[3],
        "current_period_start": row[4],
    }



async def get_user_with_billing(conn: AsyncConnection, user_id: UUID) -> dict | None:
    """Get user with billing info for credit tracking."""
    result = await conn.execute(
        text("""
        SELECT id, firebase_uid, email, role, 
               current_period_start
        FROM users WHERE id = :user_id
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "firebase_uid": row[1],
        "email": row[2],
        "role": row[3],
        "current_period_start": row[4],
    }



async def update_user_role(conn: AsyncConnection, user_id: UUID, new_role: str) -> bool:
    """Update user role. Returns True if user found."""
    result = await conn.execute(
        text("UPDATE users SET role = :role WHERE id = :user_id"),
        {"role": new_role, "user_id": user_id}
    )
    return result.rowcount > 0



async def update_user_subscription(
    conn: AsyncConnection,
    user_id: UUID,
    role: str = None,
    current_period_start: datetime = None,
) -> bool:
    """
    Update user subscription details.
    Only updates fields that are not None.
    """
    fields = []
    params = {"user_id": user_id}
    
    if role is not None:
        fields.append("role = :role")
        params["role"] = role
    if current_period_start is not None:
        fields.append("current_period_start = :period_start")
        params["period_start"] = current_period_start
        
    if not fields:
        return False
    
    query = f"""
        UPDATE users 
        SET {", ".join(fields)}
        WHERE id = :user_id
    """
    
    result = await conn.execute(text(query), params)
    await conn.commit()
    return result.rowcount > 0



async def clear_user_subscription(conn: AsyncConnection, user_id: UUID) -> bool:
    """Clear subscription data when cancelled/expired."""
    result = await conn.execute(
        text("""
        UPDATE users 
        SET role = 'free',
            current_period_start = NULL
        WHERE id = :user_id
        """),
        {"user_id": user_id}
    )
    await conn.commit()
    return result.rowcount > 0
