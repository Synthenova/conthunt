"""Database query functions for boards."""
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing
from app.core import logger
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
            WITH user_boards AS (
                SELECT b.id, b.user_id, b.name, b.created_at, b.updated_at
                FROM boards b
                WHERE b.user_id = :user_id
            ),
            board_item_agg AS (
                SELECT
                    bi.board_id,
                    COUNT(*)::int AS item_count,
                    BOOL_OR(bi.content_item_id = CAST(:check_item_id AS uuid)) AS has_item
                FROM board_items bi
                JOIN user_boards ub ON ub.id = bi.board_id
                GROUP BY bi.board_id
            ),
            recent_items AS (
                SELECT
                    bi.board_id,
                    bi.content_item_id,
                    bi.added_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY bi.board_id
                        ORDER BY bi.added_at DESC
                    ) AS rn
                FROM board_items bi
                JOIN user_boards ub ON ub.id = bi.board_id
            ),
            best_preview_asset AS (
                SELECT DISTINCT ON (ri.board_id, ri.content_item_id)
                    ri.board_id,
                    ri.added_at,
                    COALESCE(ma.gcs_uri, ma.source_url) AS preview_url
                FROM recent_items ri
                LEFT JOIN media_assets ma
                    ON ma.content_item_id = ri.content_item_id
                   AND ma.asset_type IN ('thumbnail', 'cover', 'image')
                WHERE ri.rn <= 4
                ORDER BY
                    ri.board_id,
                    ri.content_item_id,
                    CASE ma.asset_type
                        WHEN 'thumbnail' THEN 1
                        WHEN 'cover' THEN 2
                        WHEN 'image' THEN 3
                        ELSE 99
                    END,
                    ma.created_at DESC NULLS LAST
            ),
            board_preview AS (
                SELECT
                    bpa.board_id,
                    array_agg(bpa.preview_url ORDER BY bpa.added_at DESC)
                        FILTER (WHERE bpa.preview_url IS NOT NULL) AS preview_urls
                FROM best_preview_asset bpa
                GROUP BY bpa.board_id
            )
            SELECT
                ub.id,
                ub.user_id,
                ub.name,
                ub.created_at,
                ub.updated_at,
                COALESCE(bia.item_count, 0) AS item_count,
                CASE
                    WHEN :check_item_id IS NULL THEN false
                    ELSE COALESCE(bia.has_item, false)
                END AS has_item,
                bp.preview_urls
            FROM user_boards ub
            LEFT JOIN board_item_agg bia ON bia.board_id = ub.id
            LEFT JOIN board_preview bp ON bp.board_id = ub.id
            ORDER BY ub.updated_at DESC
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
    user_id: Optional[UUID] = None,
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
    
    result = await conn.execute(
        text("""
            SELECT content_item_id, id, asset_type, source_url, gcs_uri, status
            FROM media_assets
            WHERE content_item_id = ANY(:ids)
        """),
        {"ids": item_ids}
    )
    assets_result = result.fetchall()
    
    analyzed_asset_ids = set()
    if user_id:
        # Collect all video asset IDs to check analysis status
        video_asset_ids = []
        for a in assets_result:
            if a[2] == 'video':  # asset_type
                video_asset_ids.append(a[1])  # id
        
        if video_asset_ids:
            # Single batch query to check which assets are analyzed by this user
            # Uses unique index on (user_id, media_asset_id) from user_analysis_access
            analysis_result = await conn.execute(
                text("""
                    SELECT media_asset_id 
                    FROM user_analysis_access 
                    WHERE user_id = :user_id 
                    AND media_asset_id = ANY(:asset_ids)
                """),
                {"user_id": user_id, "asset_ids": video_asset_ids}
            )
            analyzed_asset_ids = {row[0] for row in analysis_result.fetchall()}

    assets_map = {}
    for a in assets_result:
        cid = a[0]
        if cid not in assets_map:
            assets_map[cid] = []
        
        asset_id = a[1]
        is_video = a[2] == 'video'
        
        assets_map[cid].append({
            "id": asset_id,
            "asset_type": a[2],
            "source_url": a[3],
            "gcs_uri": a[4],
            "status": a[5],
            "is_analyzed": is_video and asset_id in analyzed_asset_ids
        })

    for row in rows:
        cid = row[2]
        
        # Build content_item using shared helper (offset=2: skips board_id, added_at)
        content_item = content_item_from_row(row, offset=2)
        
        # Check if any asset for this item is an analyzed video
        is_analyzed = False
        item_assets = assets_map.get(cid, [])
        for asset in item_assets:
            if asset.get("is_analyzed"):
                is_analyzed = True
                break
        
        content_item["is_analyzed"] = is_analyzed
        logger.info(f"Content item {cid} is_analyzed: {is_analyzed}")
        items.append({
            "board_id": row[0],
            "added_at": row[1],
            "content_item": content_item,
            "assets": item_assets
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
    # Preserve prior behavior: an empty query returns all boards (ILIKE '%%' matched everything).
    if not query or not query.strip():
        result = await conn.execute(
            text("""
                WITH user_boards AS (
                    SELECT b.id, b.user_id, b.name, b.created_at, b.updated_at
                    FROM boards b
                    WHERE b.user_id = :user_id
                ),
                user_board_items AS (
                    SELECT bi.board_id, bi.content_item_id
                    FROM board_items bi
                    JOIN user_boards ub ON ub.id = bi.board_id
                ),
                board_counts AS (
                    SELECT ubi.board_id, COUNT(*)::int AS item_count
                    FROM user_board_items ubi
                    GROUP BY ubi.board_id
                )
                SELECT
                    ub.id,
                    ub.user_id,
                    ub.name,
                    ub.created_at,
                    ub.updated_at,
                    COALESCE(bc.item_count, 0) AS item_count
                FROM user_boards ub
                LEFT JOIN board_counts bc ON bc.board_id = ub.id
                ORDER BY ub.updated_at DESC
            """),
            {"user_id": user_id},
        )

        return [
            {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "item_count": row[5],
            }
            for row in result.fetchall()
        ]

    result = await conn.execute(
        text("""
            WITH q AS (
                SELECT websearch_to_tsquery('english', :q) AS tsq
            ),
            user_boards AS (
                SELECT b.id, b.user_id, b.name, b.created_at, b.updated_at, b.fts
                FROM boards b
                WHERE b.user_id = :user_id
            ),
            user_board_items AS (
                SELECT bi.board_id, bi.content_item_id
                FROM board_items bi
                JOIN user_boards ub ON ub.id = bi.board_id
            ),
            board_name_hits AS (
                SELECT ub.id, ts_rank(ub.fts, q.tsq) AS rank
                FROM user_boards ub
                CROSS JOIN q
                WHERE ub.fts @@ q.tsq
            ),
            content_hits AS (
                SELECT ubi.board_id AS id, MAX(ts_rank(ci.fts, q.tsq)) AS rank
                FROM user_board_items ubi
                JOIN content_items ci ON ci.id = ubi.content_item_id
                CROSS JOIN q
                WHERE ci.fts @@ q.tsq
                GROUP BY ubi.board_id
            ),
            matched_boards AS (
                SELECT id, MAX(rank) AS rank
                FROM (
                    SELECT id, rank FROM board_name_hits
                    UNION ALL
                    SELECT id, rank FROM content_hits
                ) x
                GROUP BY id
            ),
            board_counts AS (
                SELECT ubi.board_id, COUNT(*)::int AS item_count
                FROM user_board_items ubi
                JOIN matched_boards mb ON mb.id = ubi.board_id
                GROUP BY ubi.board_id
            )
            SELECT
                ub.id,
                ub.user_id,
                ub.name,
                ub.created_at,
                ub.updated_at,
                COALESCE(bc.item_count, 0) AS item_count
            FROM user_boards ub
            JOIN matched_boards mb ON mb.id = ub.id
            LEFT JOIN board_counts bc ON bc.board_id = ub.id
            ORDER BY mb.rank DESC, ub.updated_at DESC
        """),
        {"user_id": user_id, "q": query}
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
    # Preserve prior behavior: an empty query returns all items in the board.
    if not query or not query.strip():
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
            {"board_id": board_id},
        )
        rows = result.fetchall()
    else:
        result = await conn.execute(
            text("""
                WITH q AS (
                    SELECT websearch_to_tsquery('english', :q) AS tsq
                )
                SELECT
                    bi.board_id, bi.added_at,
                    ci.id, ci.platform, ci.external_id, ci.content_type,
                    ci.canonical_url, ci.title, ci.primary_text, ci.published_at,
                    ci.creator_handle, ci.author_id, ci.author_name, ci.author_url, ci.author_image_url,
                    ci.metrics
                FROM board_items bi
                JOIN content_items ci ON bi.content_item_id = ci.id
                CROSS JOIN q
                WHERE bi.board_id = :board_id
                  AND ci.fts @@ q.tsq
                ORDER BY ts_rank(ci.fts, q.tsq) DESC, bi.added_at DESC
            """),
            {"board_id": board_id, "q": query},
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
