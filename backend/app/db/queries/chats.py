from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing

from app.schemas.chats import Chat as ChatSchema

@log_query_timing
async def create_chat(
    conn: AsyncConnection,
    chat_id: UUID,
    user_id: UUID,
    thread_id: str,
    title: str,
    context_type: Optional[str] = None,
    context_id: Optional[UUID] = None,
) -> None:
    """Insert a new chat record."""
    await conn.execute(
        text("""
            INSERT INTO conthunt.chats (id, user_id, thread_id, title, status, context_type, context_id)
            VALUES (:id, :user_id, :thread_id, :title, 'idle', :context_type, :context_id)
        """),
        {
            "id": chat_id,
            "user_id": user_id,
            "thread_id": thread_id,
            "title": title,
            "context_type": context_type,
            "context_id": context_id,
        }
    )


@log_query_timing
async def get_user_chats(
    conn: AsyncConnection,
    user_id: UUID,
    context_type: Optional[str] = None,
    context_id: Optional[UUID] = None,
) -> List[ChatSchema]:
    """Get all chats for a user."""
    # Note: RLS handles the filtering usually, but we include user_id in query for explicit correctness if bypassing RLS
    # Here we assume RLS is set, but standard select is good.
    where_clauses = ["deleted_at IS NULL"]
    params: dict = {}
    if context_type:
        where_clauses.append("context_type = :context_type")
        params["context_type"] = context_type
    if context_id:
        where_clauses.append("context_id = :context_id")
        params["context_id"] = context_id

    where_sql = " AND ".join(where_clauses)
    rows = await conn.execute(
        text("""
            SELECT id, user_id, thread_id, title, context_type, context_id, status, created_at, updated_at
            FROM conthunt.chats 
            WHERE """ + where_sql + """
            ORDER BY updated_at DESC
        """),
        params
    )
    
    results = []
    for r in rows:
        results.append(ChatSchema(
            id=r[0],
            user_id=r[1],
            thread_id=r[2],
            title=r[3],
            context_type=r[4],
            context_id=r[5],
            status=r[6],
            created_at=r[7],
            updated_at=r[8]
        ))
    return results

@log_query_timing
async def get_chat_thread_id(conn: AsyncConnection, chat_id: UUID) -> Optional[str]:
    """Get thread_id for a chat."""
    row = await conn.execute(
        text("SELECT thread_id FROM conthunt.chats WHERE id = :id"),
        {"id": chat_id}
    )
    res = row.fetchone()
    return res[0] if res else None

@log_query_timing
async def check_chat_exists(conn: AsyncConnection, chat_id: UUID) -> bool:
    """Check if a chat exists."""
    row = await conn.execute(
        text("SELECT 1 FROM conthunt.chats WHERE id = :id AND deleted_at IS NULL"),
        {"id": chat_id}
    )
    return bool(row.fetchone())


@log_query_timing
async def delete_chat(conn: AsyncConnection, chat_id: UUID) -> None:
    """Soft delete a chat."""
    await conn.execute(
        text("UPDATE conthunt.chats SET deleted_at = NOW() WHERE id = :id"),
        {"id": chat_id}
    )
