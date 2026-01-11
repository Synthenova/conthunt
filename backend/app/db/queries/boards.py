"""Database query functions for boards."""
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing

from app.services.content_builder import content_item_from_row



async def create_board(
    conn: AsyncConnection,
    user_id: UUID,
    name: str,
) -> UUID:
    """Create a new board."""
    board_id = uuid4()
    await conn.execute(
        text("""
            INSERT INTO boards (id, user_id, name)
            VALUES (:id, :user_id, :name)
        """),
        {"id": board_id, "user_id": user_id, "name": name}
    )
    return board_id



async def get_user_boards(
    conn: AsyncConnection,
    user_id: UUID,
    check_content_item_id: Optional[UUID] = None,
) -> List[dict]:
    """
    Get all boards for a user with item counts.
    RLS protects access, but we filter by user_id explicitly for clarity/optimization index usage.
    """
    result = await conn.execute(
        text("""
            SELECT 
                b.id, b.user_id, b.name, b.created_at, b.updated_at,
                (SELECT COUNT(*) FROM board_items bi WHERE bi.board_id = b.id) as item_count,
                case when cast(:check_item_id as uuid) is not null then
                    exists(select 1 from board_items bi where bi.board_id = b.id and bi.content_item_id = :check_item_id)
                else false end as has_item,
                preview.preview_urls
            FROM boards b
            LEFT JOIN LATERAL (
                SELECT array_agg(item.preview_url ORDER BY item.added_at DESC) AS preview_urls
                FROM (
                    SELECT
                        bi.added_at,
                        COALESCE(best_asset.gcs_uri, best_asset.source_url) AS preview_url
                    FROM board_items bi
                    LEFT JOIN LATERAL (
                        SELECT ma.gcs_uri, ma.source_url
                        FROM media_assets ma
                        WHERE ma.content_item_id = bi.content_item_id
                          AND ma.asset_type IN ('thumbnail', 'cover', 'image')
                        ORDER BY
                            CASE ma.asset_type
                                WHEN 'thumbnail' THEN 1
                                WHEN 'cover' THEN 2
                                WHEN 'image' THEN 3
                                ELSE 99
                            END
                        LIMIT 1
                    ) best_asset ON true
                    WHERE bi.board_id = b.id
                    ORDER BY bi.added_at DESC
                    LIMIT 4
                ) item
                WHERE item.preview_url IS NOT NULL
            ) preview ON true
            WHERE b.user_id = :user_id
            ORDER BY b.updated_at DESC
        """),
        {"user_id": user_id, "check_item_id": check_content_item_id}
    )
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "item_count": row[5],
            "has_item": row[6],
            "preview_urls": list(row[7] or []),
        }
        for row in result.fetchall()
    ]



async def get_board_by_id(
    conn: AsyncConnection,
    board_id: UUID,
) -> dict | None:
    """Get a single board with item count (single query, no N+1)."""
    result = await conn.execute(
        text("""
            SELECT b.id, b.user_id, b.name, b.created_at, b.updated_at,
                   COUNT(bi.content_item_id) as item_count
            FROM boards b
            LEFT JOIN board_items bi ON b.id = bi.board_id
            WHERE b.id = :id
            GROUP BY b.id
        """),
        {"id": board_id}
    )
    row = result.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "item_count": row[5]
    }



async def delete_board(
    conn: AsyncConnection,
    board_id: UUID,
) -> bool:
    """Delete a board. Returns True if deleted."""
    result = await conn.execute(
        text("DELETE FROM boards WHERE id = :id"),
        {"id": board_id}
    )
    return result.rowcount > 0



async def add_item_to_board(
    conn: AsyncConnection,
    board_id: UUID,
    content_item_id: UUID,
) -> bool:
    """Add item to board. Returns True if added (false if exists)."""
    # RLS ensures user owns the board (via subquery policy on board_items)
    try:
        await conn.execute(
            text("""
                INSERT INTO board_items (board_id, content_item_id)
                VALUES (:board_id, :content_item_id)
                ON CONFLICT (board_id, content_item_id) DO NOTHING
            """),
            {"board_id": board_id, "content_item_id": content_item_id}
        )
        # Update board updated_at
        await conn.execute(
            text("UPDATE boards SET updated_at = now() WHERE id = :id"),
            {"id": board_id}
        )
        return True
    except Exception:
        # Should catch specific integrity errors ideally, but RLS might raise simple auth errors or check violations
        raise



async def batch_add_items_to_board(
    conn: AsyncConnection,
    board_id: UUID,
    content_item_ids: List[UUID],
) -> int:
    """
    Add multiple items to a board in a single query.
    
    Returns the number of items actually inserted (excludes duplicates).
    """
    if not content_item_ids:
        return 0
    
    # Use unnest for efficient batch insert
    result = await conn.execute(
        text("""
            INSERT INTO board_items (board_id, content_item_id)
            SELECT :board_id, unnest(CAST(:content_item_ids AS UUID[]))
            ON CONFLICT (board_id, content_item_id) DO NOTHING
        """),
        {"board_id": board_id, "content_item_ids": content_item_ids}
    )
    
    # Update board updated_at
    await conn.execute(
        text("UPDATE boards SET updated_at = now() WHERE id = :id"),
        {"id": board_id}
    )
    
    return result.rowcount



async def remove_item_from_board(
    conn: AsyncConnection,
    board_id: UUID,
    content_item_id: UUID,
) -> bool:
    """Remove item from board."""
    result = await conn.execute(
        text("""
            DELETE FROM board_items 
            WHERE board_id = :board_id AND content_item_id = :content_item_id
        """),
        {"board_id": board_id, "content_item_id": content_item_id}
    )
    return result.rowcount > 0



async def get_board_items(
    conn: AsyncConnection,
    board_id: UUID,
) -> List[dict]:
    """Get all items in a board with content details."""
    result = await conn.execute(
        text("""
            SELECT 
                bi.board_id, bi.added_at,
                ci.id, ci.platform, ci.external_id, ci.content_type,
                ci.canonical_url, ci.title, ci.primary_text, ci.published_at,
                ci.creator_handle, ci.author_id, ci.author_name, ci.author_url, ci.author_image_url,
                ci.metrics
            FROM board_items bi
            JOIN content_items ci ON bi.content_item_id = ci.id
            WHERE bi.board_id = :board_id
            ORDER BY bi.added_at DESC
        """),
        {"board_id": board_id}
    )
    
    items = []
    rows = result.fetchall()
    
    if not rows:
        return []

    item_ids = [row[2] for row in rows]
    
    assets_result = await conn.execute(
        text("""
            SELECT content_item_id, id, asset_type, source_url, gcs_uri, status
            FROM media_assets
            WHERE content_item_id = ANY(:ids)
        """),
        {"ids": item_ids}
    )
    
    assets_map = {}
    for a in assets_result.fetchall():
        cid = a[0]
        if cid not in assets_map:
            assets_map[cid] = []
        assets_map[cid].append({
            "id": a[1],
            "asset_type": a[2],
            "source_url": a[3],
            "gcs_uri": a[4],
            "status": a[5],
        })

    for row in rows:
        cid = row[2]
        
        # Build content_item using shared helper (offset=2: skips board_id, added_at)
        content_item = content_item_from_row(row, offset=2)

        items.append({
            "board_id": row[0],
            "added_at": row[1],
            "content_item": content_item,
            "assets": assets_map.get(cid, [])
        })
        
    return items



async def get_board_items_summary(
    conn: AsyncConnection,
    board_id: UUID,
) -> List[dict]:
    """
    Get board items for agent consumption - minimal text data + video media_asset_id only.
    No URLs, thumbnails, or other non-essential data.
    """
    result = await conn.execute(
        text("""
            SELECT 
                ci.title,
                ci.platform,
                ci.creator_handle,
                ci.content_type,
                ci.primary_text,
                ma.id as media_asset_id
            FROM board_items bi
            JOIN content_items ci ON bi.content_item_id = ci.id
            LEFT JOIN media_assets ma ON ma.content_item_id = ci.id AND ma.asset_type = 'video'
            WHERE bi.board_id = :board_id
            ORDER BY bi.added_at DESC
        """),
        {"board_id": board_id}
    )
    
    items = []
    for row in result.fetchall():
        items.append({
            "title": row[0],
            "platform": row[1],
            "creator_handle": row[2],
            "content_type": row[3],
            "primary_text": row[4],
            "media_asset_id": str(row[5]) if row[5] else None,
        })
        
    return items



async def search_user_boards(
    conn: AsyncConnection,
    user_id: UUID,
    query: str,
) -> List[dict]:
    """
    Search boards by name OR by content items within them.
    Returns list of boards that match.
    """
    pattern = f"%{query}%"
    result = await conn.execute(
        text("""
            SELECT DISTINCT b.id, b.user_id, b.name, b.created_at, b.updated_at,
                   (SELECT COUNT(*) FROM board_items bi WHERE bi.board_id = b.id) as item_count
            FROM boards b
            LEFT JOIN board_items bi ON b.id = bi.board_id
            LEFT JOIN content_items ci ON bi.content_item_id = ci.id
            WHERE b.user_id = :user_id
              AND (
                b.name ILIKE :pattern
                OR ci.title ILIKE :pattern
                OR ci.primary_text ILIKE :pattern
              )
            ORDER BY b.updated_at DESC
        """),
        {"user_id": user_id, "pattern": pattern}
    )
    
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "item_count": row[5]
        }
        for row in result.fetchall()
    ]



async def search_in_board(
    conn: AsyncConnection,
    board_id: UUID,
    query: str,
) -> List[dict]:
    """Search for content items strictly within a board."""
    pattern = f"%{query}%"
    result = await conn.execute(
        text("""
            SELECT 
                bi.board_id, bi.added_at,
                ci.id, ci.platform, ci.external_id, ci.content_type,
                ci.canonical_url, ci.title, ci.primary_text, ci.published_at,
                ci.creator_handle, ci.author_id, ci.author_name, ci.author_url, ci.author_image_url,
                ci.metrics
            FROM board_items bi
            JOIN content_items ci ON bi.content_item_id = ci.id
            WHERE bi.board_id = :board_id
              AND (
                ci.title ILIKE :pattern
                OR ci.primary_text ILIKE :pattern
              )
            ORDER BY bi.added_at DESC
        """),
        {"board_id": board_id, "pattern": pattern}
    )
    
    rows = result.fetchall()
    if not rows:
        return []
        
    item_ids = [row[2] for row in rows]
    assets_result = await conn.execute(
        text("""
            SELECT content_item_id, id, asset_type, source_url, gcs_uri, status
            FROM media_assets
            WHERE content_item_id = ANY(:ids)
        """),
        {"ids": item_ids}
    )
    
    assets_map = {}
    for a in assets_result.fetchall():
        cid = a[0]
        if cid not in assets_map:
            assets_map[cid] = []
        assets_map[cid].append({
            "id": a[1],
            "asset_type": a[2],
            "source_url": a[3],
            "gcs_uri": a[4],
            "status": a[5],
        })

    items = []
    for row in rows:
        cid = row[2]
        
        # Build content_item using shared helper (offset=2: skips board_id, added_at)
        content_item = content_item_from_row(row, offset=2)

        items.append({
            "board_id": row[0],
            "added_at": row[1],
            "content_item": content_item,
            "assets": assets_map.get(cid, [])
        })

    return items
