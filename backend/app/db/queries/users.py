"""User-related database queries."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_user_role(conn: AsyncConnection, user_id: UUID) -> str:
    """Get user's current role."""
    result = await conn.execute(
        text("SELECT role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    return row[0] if row else "free"


async def update_user_role(
    conn: AsyncConnection, 
    firebase_uid: str, 
    new_role: str
) -> bool:
    """Update user role by Firebase UID. Returns True if user found."""
    result = await conn.execute(
        text("UPDATE users SET role = :role WHERE firebase_uid = :uid"),
        {"role": new_role, "uid": firebase_uid}
    )
    return result.rowcount > 0


async def update_user_dodo_subscription(
    conn: AsyncConnection,
    firebase_uid: str,
    role: str = None,
    customer_id: str = None,
    subscription_id: str = None,
    product_id: str = None,
    status: str = None,
) -> bool:
    """
    Update user Dodo subscription details and role.
    Only updates fields that are not None.
    """
    # Construct dynamic update query
    fields = []
    params = {"uid": firebase_uid}
    
    if role is not None:
        fields.append("role = :role")
        params["role"] = role
    if customer_id is not None:
        fields.append("dodo_customer_id = :customer_id")
        params["customer_id"] = customer_id
    if subscription_id is not None:
        fields.append("dodo_subscription_id = :subscription_id")
        params["subscription_id"] = subscription_id
    if product_id is not None:
        fields.append("dodo_product_id = :product_id")
        params["product_id"] = product_id
    if status is not None:
        fields.append("dodo_status = :status")
        params["status"] = status
        
    if not fields:
        return False
        
    fields.append("dodo_updated_at = now()")
    
    query = f"""
        UPDATE users 
        SET {", ".join(fields)}
        WHERE firebase_uid = :uid
    """
    
    result = await conn.execute(text(query), params)
    return result.rowcount > 0
