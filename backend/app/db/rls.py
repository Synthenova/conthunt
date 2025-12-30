"""Row Level Security (RLS) helpers."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing


# @log_query_timing
async def set_rls_user(conn: AsyncConnection, user_uuid: UUID) -> None:
    """
    Set the app.user_id config for RLS policies.
    
    This must be called within a transaction before any queries
    that should be filtered by RLS.
    """
    await conn.execute(
        text("SELECT set_config('app.user_id', :uid, true)"),
        {"uid": str(user_uuid)}
    )
