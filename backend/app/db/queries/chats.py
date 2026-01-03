import json
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
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

@log_query_timing
async def update_chat_title(
    conn: AsyncConnection,
    chat_id: UUID,
    title: str,
) -> Optional[ChatSchema]:
    """Update a chat title and return the updated record."""
    row = await conn.execute(
        text("""
            UPDATE conthunt.chats
            SET title = :title,
                updated_at = NOW()
            WHERE id = :id
              AND deleted_at IS NULL
            RETURNING id, user_id, thread_id, title, context_type, context_id, status, created_at, updated_at
        """),
        {"id": chat_id, "title": title}
    )
    res = row.fetchone()
    if not res:
        return None
    return ChatSchema(
        id=res[0],
        user_id=res[1],
        thread_id=res[2],
        title=res[3],
        context_type=res[4],
        context_id=res[5],
        status=res[6],
        created_at=res[7],
        updated_at=res[8],
    )


@log_query_timing
async def upsert_chat_tags(
    conn: AsyncConnection,
    chat_id: UUID,
    tags: List[dict],
) -> None:
    """Upsert tags for a chat. Deduplicates on (chat_id, tag_type, tag_id)."""
    if not tags:
        return

    # Determine a top sort_order to keep newest tags on top when none provided
    top_order_row = await conn.execute(
        text("""
            SELECT MIN(sort_order) AS min_order
            FROM conthunt.chat_tags
            WHERE chat_id = :chat_id
        """),
        {"chat_id": chat_id}
    )
    min_order = top_order_row.scalar()
    next_top = (min_order - 1) if min_order is not None else -1

    prepared = []
    for tag in tags:
        sort_order = tag.get("sort_order")
        if sort_order is None:
            sort_order = next_top
            next_top -= 1

        prepared.append({
            "id": str(tag.get("id") or uuid4()),
            "chat_id": str(chat_id),
            "tag_type": tag["type"],
            "tag_id": str(tag["tag_id"]),
            "tag_label": tag.get("label"),
            "source": tag.get("source", "user"),
            "sort_order": sort_order,
        })

    await conn.execute(
        text("""
            INSERT INTO conthunt.chat_tags (id, chat_id, tag_type, tag_id, tag_label, source, sort_order)
            SELECT id, chat_id, tag_type, tag_id, tag_label, source, sort_order
            FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS x(
                id uuid,
                chat_id uuid,
                tag_type text,
                tag_id uuid,
                tag_label text,
                source text,
                sort_order int
            )
            ON CONFLICT (chat_id, tag_type, tag_id) DO UPDATE
            SET tag_label = COALESCE(EXCLUDED.tag_label, conthunt.chat_tags.tag_label),
                source = EXCLUDED.source,
                sort_order = EXCLUDED.sort_order
        """),
        {"data": json.dumps(prepared)}
    )


@log_query_timing
async def get_chat_tags(
    conn: AsyncConnection,
    chat_id: UUID,
) -> List[dict]:
    """Fetch tags for a chat."""
    rows = await conn.execute(
        text("""
            SELECT id, tag_type, tag_id, tag_label, source, created_at, sort_order
            FROM conthunt.chat_tags
            WHERE chat_id = :chat_id
            ORDER BY sort_order ASC NULLS LAST, created_at DESC
        """),
        {"chat_id": chat_id}
    )
    return [
        {
            "id": r[0],
            "type": r[1],
            "tag_id": r[2],
            "label": r[3],
            "source": r[4],
            "created_at": r[5],
            "sort_order": r[6],
        }
        for r in rows
    ]


@log_query_timing
async def update_chat_tag_orders(
    conn: AsyncConnection,
    chat_id: UUID,
    orders: List[dict],
) -> None:
    """Update sort_order for multiple tags in a chat."""
    if not orders:
        return
    prepared = [
        {"chat_id": str(chat_id), "tag_id": str(o["tag_id"]), "sort_order": int(o["sort_order"])}
        for o in orders
    ]
    await conn.execute(
        text("""
            UPDATE conthunt.chat_tags AS ct
            SET sort_order = data.sort_order
            FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS data(
                chat_id uuid,
                tag_id uuid,
                sort_order int
            )
            WHERE ct.chat_id = data.chat_id AND ct.tag_id = data.tag_id
        """),
        {"data": json.dumps(prepared)}
    )
