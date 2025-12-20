"""Database query functions for TwelveLabs video analysis."""
import json
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection



async def get_twelvelabs_asset_by_content_item(
    conn: AsyncConnection,
    content_item_id: UUID,
) -> dict | None:
    """Get TwelveLabs asset by content_item_id."""
    result = await conn.execute(
        text("""
            SELECT id, content_item_id, asset_id, indexed_asset_id,
                   asset_status, index_status, error, index_id
            FROM twelvelabs_assets
            WHERE content_item_id = :content_item_id
        """),
        {"content_item_id": content_item_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "content_item_id": row[1],
        "asset_id": row[2],
        "indexed_asset_id": row[3],
        "asset_status": row[4],
        "index_status": row[5],
        "error": row[6],
        "index_id": row[7],
    }


async def upsert_twelvelabs_asset(
    conn: AsyncConnection,
    content_item_id: UUID,
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
                id, content_item_id, index_id, asset_id, asset_status, upload_raw_gcs_uri
            )
            VALUES (:id, :content_item_id, :index_id, :asset_id, :asset_status, :upload_raw_gcs_uri)
            ON CONFLICT (content_item_id) DO UPDATE SET
                asset_id = EXCLUDED.asset_id,
                asset_status = EXCLUDED.asset_status,
                upload_raw_gcs_uri = COALESCE(EXCLUDED.upload_raw_gcs_uri, twelvelabs_assets.upload_raw_gcs_uri),
                updated_at = now()
            RETURNING id
        """),
        {
            "id": uuid4(),
            "content_item_id": content_item_id,
            "index_id": index_id,
            "asset_id": asset_id,
            "asset_status": asset_status,
            "upload_raw_gcs_uri": upload_raw_gcs_uri,
        }
    )
    return result.fetchone()[0]



async def update_twelvelabs_asset_status(
    conn: AsyncConnection,
    content_item_id: UUID,
    asset_status: str | None = None,
    indexed_asset_id: str | None = None,
    index_status: str | None = None,
    error: str | None = None,
    index_raw_gcs_uri: str | None = None,
) -> None:
    """Update TwelveLabs asset status fields."""
    updates = ["updated_at = now()"]
    params = {"content_item_id": content_item_id}
    
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
            WHERE content_item_id = :content_item_id
        """),
        params
    )


async def get_video_analysis_by_content_item(
    conn: AsyncConnection,
    content_item_id: UUID,
) -> dict | None:
    """Get cached video analysis for a content item."""
    result = await conn.execute(
        text("""
            SELECT id, content_item_id, twelvelabs_asset_id, prompt,
                   analysis_result, token_usage, created_at
            FROM video_analyses
            WHERE content_item_id = :content_item_id
        """),
        {"content_item_id": content_item_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "content_item_id": row[1],
        "twelvelabs_asset_id": row[2],
        "prompt": row[3],
        "analysis_result": row[4],
        "token_usage": row[5],
        "created_at": row[6],
    }


async def insert_video_analysis(
    conn: AsyncConnection,
    content_item_id: UUID,
    twelvelabs_asset_id: UUID | None,
    prompt: str,
    analysis_result: dict,
    token_usage: int | None = None,
    raw_gcs_uri: str | None = None,
) -> UUID:
    """Insert a video analysis result."""
    analysis_id = uuid4()
    await conn.execute(
        text("""
            INSERT INTO video_analyses (
                id, content_item_id, twelvelabs_asset_id, prompt,
                analysis_result, token_usage, raw_gcs_uri
            )
            VALUES (
                :id, :content_item_id, :twelvelabs_asset_id, :prompt,
                :analysis_result, :token_usage, :raw_gcs_uri
            )
        """),
        {
            "id": analysis_id,
            "content_item_id": content_item_id,
            "twelvelabs_asset_id": twelvelabs_asset_id,
            "prompt": prompt,
            "analysis_result": json.dumps(analysis_result),
            "token_usage": token_usage,
            "raw_gcs_uri": raw_gcs_uri,
        }
    )
    return analysis_id


async def get_user_twelvelabs_assets(
    conn: AsyncConnection,
) -> List[str]:
    """Get all TwelveLabs indexed asset IDs for a user's boards (RLS implicit)."""
    result = await conn.execute(
        text("""
            SELECT DISTINCT ta.indexed_asset_id
            FROM twelvelabs_assets ta
            JOIN content_items ci ON ta.content_item_id = ci.id
            JOIN board_items bi ON ci.id = bi.content_item_id
            JOIN boards b ON bi.board_id = b.id
            WHERE ta.indexed_asset_id IS NOT NULL
        """)
    )
    rows = result.fetchall()
    return [row[0] for row in rows]

