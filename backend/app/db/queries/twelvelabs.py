"""Database query functions for TwelveLabs video analysis."""
import json
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing



async def get_twelvelabs_asset_by_media_asset(
    conn: AsyncConnection,
    media_asset_id: UUID,
) -> dict | None:
    """Get TwelveLabs asset by media_asset_id."""
    result = await conn.execute(
        text("""
            SELECT id, media_asset_id, asset_id, indexed_asset_id,
                   asset_status, index_status, error, index_id
            FROM twelvelabs_assets
            WHERE media_asset_id = :media_asset_id
        """),
        {"media_asset_id": media_asset_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "media_asset_id": row[1],
        "asset_id": row[2],
        "indexed_asset_id": row[3],
        "asset_status": row[4],
        "index_status": row[5],
        "error": row[6],
        "index_id": row[7],
    }



async def upsert_twelvelabs_asset(
    conn: AsyncConnection,
    media_asset_id: UUID,
    index_id: str,
    asset_id: str,
    asset_status: str = "pending",
    upload_raw_gcs_uri: str | None = None,
) -> UUID:
    """
    Insert or update a TwelveLabs asset record.
    
    Returns the internal UUID.
    """
    result = await conn.execute(
        text("""
            INSERT INTO twelvelabs_assets (
                id, media_asset_id, index_id, asset_id, asset_status, upload_raw_gcs_uri
            )
            VALUES (:id, :media_asset_id, :index_id, :asset_id, :asset_status, :upload_raw_gcs_uri)
            ON CONFLICT (media_asset_id) DO UPDATE SET
                asset_id = EXCLUDED.asset_id,
                asset_status = EXCLUDED.asset_status,
                upload_raw_gcs_uri = COALESCE(EXCLUDED.upload_raw_gcs_uri, twelvelabs_assets.upload_raw_gcs_uri),
                updated_at = now()
            RETURNING id
        """),
        {
            "id": uuid4(),
            "media_asset_id": media_asset_id,
            "index_id": index_id,
            "asset_id": asset_id,
            "asset_status": asset_status,
            "upload_raw_gcs_uri": upload_raw_gcs_uri,
        }
    )
    return result.fetchone()[0]




async def update_twelvelabs_asset_status(
    conn: AsyncConnection,
    media_asset_id: UUID,
    asset_status: str | None = None,
    indexed_asset_id: str | None = None,
    index_status: str | None = None,
    error: str | None = None,
    index_raw_gcs_uri: str | None = None,
) -> None:
    """Update TwelveLabs asset status fields."""
    updates = ["updated_at = now()"]
    params = {"media_asset_id": media_asset_id}
    
    if asset_status is not None:
        updates.append("asset_status = :asset_status")
        params["asset_status"] = asset_status
    if indexed_asset_id is not None:
        updates.append("indexed_asset_id = :indexed_asset_id")
        params["indexed_asset_id"] = indexed_asset_id
    if index_status is not None:
        updates.append("index_status = :index_status")
        params["index_status"] = index_status
    if error is not None:
        updates.append("error = :error")
        params["error"] = error
    if index_raw_gcs_uri is not None:
        updates.append("index_raw_gcs_uri = :index_raw_gcs_uri")
        params["index_raw_gcs_uri"] = index_raw_gcs_uri
    
    await conn.execute(
        text(f"""
            UPDATE twelvelabs_assets
            SET {', '.join(updates)}
            WHERE media_asset_id = :media_asset_id
        """),
        params
    )



async def get_user_twelvelabs_assets(
    conn: AsyncConnection,
) -> List[str]:
    """
    Get all TwelveLabs indexed asset IDs for a user's boards.
    
    Optimized: Uses subquery to reduce JOINs from 5 to 3.
    RLS on board_items implicitly filters by user.
    """
    result = await conn.execute(
        text("""
            SELECT DISTINCT ta.indexed_asset_id
            FROM twelvelabs_assets ta
            WHERE ta.indexed_asset_id IS NOT NULL
              AND ta.media_asset_id IN (
                  SELECT ma.id
                  FROM media_assets ma
                  JOIN board_items bi ON ma.content_item_id = bi.content_item_id
              )
        """)
    )
    rows = result.fetchall()
    return [row[0] for row in rows]



async def get_board_twelvelabs_assets(
    conn: AsyncConnection,
    board_id: UUID,
) -> List[str]:
    """
    Get TwelveLabs indexed asset IDs for a specific board.
    
    Optimized: Removed content_items JOIN (not needed for this query).
    """
    result = await conn.execute(
        text("""
            SELECT DISTINCT ta.indexed_asset_id
            FROM twelvelabs_assets ta
            JOIN media_assets ma ON ta.media_asset_id = ma.id
            JOIN board_items bi ON ma.content_item_id = bi.content_item_id
            WHERE bi.board_id = :board_id
              AND ta.indexed_asset_id IS NOT NULL
        """),
        {"board_id": board_id}
    )
    return [row[0] for row in result.fetchall()]



async def get_twelvelabs_id_for_media_asset(
    conn: AsyncConnection,
    media_asset_id: UUID,
) -> str | None:
    """Get the TwelveLabs indexed_asset_id for a given media_asset_id."""
    result = await conn.execute(
        text("""
            SELECT indexed_asset_id
            FROM twelvelabs_assets
            WHERE media_asset_id = :media_asset_id
              AND indexed_asset_id IS NOT NULL
        """),
        {"media_asset_id": media_asset_id}
    )
    row = result.fetchone()
    return row[0] if row else None



async def resolve_indexed_asset_ids_to_media(
    conn: AsyncConnection,
    indexed_asset_ids: list[str],
) -> dict[str, dict]:
    """
    Resolve a list of TwelveLabs indexed_asset_ids to media asset details.
    
    Returns a dict mapping indexed_asset_id -> {media_asset_id, title, platform}.
    """
    if not indexed_asset_ids:
        return {}
    
    result = await conn.execute(
        text("""
            SELECT 
                ta.indexed_asset_id,
                ta.media_asset_id,
                ci.title,
                ci.platform
            FROM twelvelabs_assets ta
            JOIN media_assets ma ON ta.media_asset_id = ma.id
            JOIN content_items ci ON ma.content_item_id = ci.id
            WHERE ta.indexed_asset_id = ANY(:ids)
        """),
        {"ids": indexed_asset_ids}
    )
    
    mapping = {}
    for row in result.fetchall():
        mapping[row[0]] = {
            "media_asset_id": str(row[1]),
            "title": row[2],
            "platform": row[3],
        }
    return mapping

