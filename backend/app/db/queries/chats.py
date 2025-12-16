from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.schemas.chats import Chat as ChatSchema

async def create_chat(
    conn: AsyncConnection,
    chat_id: UUID,
    user_id: UUID,
    thread_id: str,
    title: str,
) -> None:
    """Insert a new chat record."""
    await conn.execute(
        text("""
            INSERT INTO conthunt.chats (id, user_id, thread_id, title, status)
            VALUES (:id, :user_id, :thread_id, :title, 'idle')
        """),
        {
            "id": chat_id,
            "user_id": user_id,
            "thread_id": thread_id,
            "title": title
        }
    )


async def get_user_chats(conn: AsyncConnection, user_id: UUID) -> List[ChatSchema]:
    """Get all chats for a user."""
    # Note: RLS handles the filtering usually, but we include user_id in query for explicit correctness if bypassing RLS
    # Here we assume RLS is set, but standard select is good.
    rows = await conn.execute(
        text("""
            SELECT id, user_id, thread_id, title, status, created_at, updated_at 
            FROM conthunt.chats 
            WHERE deleted_at IS NULL
            ORDER BY updated_at DESC
        """)
    )
    
    results = []
    for r in rows:
        results.append(ChatSchema(
            id=r[0],
            user_id=r[1],
            thread_id=r[2],
            title=r[3],
            status=r[4],
            created_at=r[5],
            updated_at=r[6]
        ))
    return results

async def get_chat_thread_id(conn: AsyncConnection, chat_id: UUID) -> Optional[str]:
    """Get thread_id for a chat."""
    row = await conn.execute(
        text("SELECT thread_id FROM conthunt.chats WHERE id = :id"),
        {"id": chat_id}
    )
    res = row.fetchone()
    return res[0] if res else None

async def check_chat_exists(conn: AsyncConnection, chat_id: UUID) -> bool:
    """Check if a chat exists."""
    row = await conn.execute(
        text("SELECT 1 FROM conthunt.chats WHERE id = :id"),
        {"id": chat_id}
    )
    return bool(row.fetchone())
