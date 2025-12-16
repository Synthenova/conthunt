"""Database query functions for boards."""
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


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
) -> List[dict]:
    """
    Get all boards for a user with item counts.
    RLS protects access, but we filter by user_id explicitly for clarity/optimization index usage.
    """
    result = await conn.execute(
        text("""
            SELECT b.id, b.user_id, b.name, b.created_at, b.updated_at,
                   COUNT(bi.content_item_id) as item_count
            FROM boards b
            LEFT JOIN board_items bi ON b.id = bi.board_id
            WHERE b.user_id = :user_id
            GROUP BY b.id
            ORDER BY b.updated_at DESC
        """),
        {"user_id": user_id}
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


async def get_board_by_id(
    conn: AsyncConnection,
    board_id: UUID,
) -> dict | None:
    """Get a single board."""
    result = await conn.execute(
        text("""
            SELECT id, user_id, name, created_at, updated_at
            FROM boards
            WHERE id = :id
        """),
        {"id": board_id}
    )
    row = result.fetchone()
    if not row:
        return None
    
    # Get item count separately or could joint above
    count_res = await conn.execute(
        text("SELECT COUNT(*) FROM board_items WHERE board_id = :id"),
        {"id": board_id}
    )
    item_count = count_res.scalar()
    
    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "item_count": item_count
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
                ci.creator_handle, ci.metrics, ci.payload
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
            SELECT content_item_id, id, asset_type, source_url, gcs_uri, status, sha256, mime_type, bytes
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
            "sha256": a[6],
            "mime_type": a[7],
            "bytes": a[8],
        })

    for row in rows:
        cid = row[2]
        items.append({
            "board_id": row[0],
            "added_at": row[1],
            "content_item": {
                "id": cid,
                "platform": row[3],
                "external_id": row[4],
                "content_type": row[5],
                "canonical_url": row[6],
                "title": row[7],
                "primary_text": row[8],
                "published_at": row[9],
                "creator_handle": row[10],
                "metrics": row[11],
                "payload": row[12],
            },
            "assets": assets_map.get(cid, [])
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
                ci.creator_handle, ci.metrics, ci.payload
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
            SELECT content_item_id, id, asset_type, source_url, gcs_uri, status, sha256, mime_type, bytes
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
            "sha256": a[6],
            "mime_type": a[7],
            "bytes": a[8],
        })

    items = []
    for row in rows:
        cid = row[2]
        items.append({
            "board_id": row[0],
            "added_at": row[1],
            "content_item": {
                "id": cid,
                "platform": row[3],
                "external_id": row[4],
                "content_type": row[5],
                "canonical_url": row[6],
                "title": row[7],
                "primary_text": row[8],
                "published_at": row[9],
                "creator_handle": row[10],
                "metrics": row[11],
                "payload": row[12],
            },
            "assets": assets_map.get(cid, [])
        })

    return items
