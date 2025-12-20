"""Database query functions for video analysis (Gemini-based)."""
import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_video_analysis_by_media_asset(
    conn: AsyncConnection,
    media_asset_id: UUID,
) -> dict | None:
    """Get cached video analysis for a media asset."""
    result = await conn.execute(
        text("""
            SELECT id, media_asset_id, twelvelabs_asset_id, prompt,
                   analysis_result, token_usage, created_at, status, error
            FROM video_analyses
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
        "twelvelabs_asset_id": row[2],
        "prompt": row[3],
        "analysis_result": row[4],
        "token_usage": row[5],
        "created_at": row[6],
        "status": row[7],
        "error": row[8],
    }


async def create_pending_analysis(
    conn: AsyncConnection,
    media_asset_id: UUID,
    prompt: str,
) -> UUID:
    """Create a pending analysis record (status='processing')."""
    analysis_id = uuid4()
    await conn.execute(
        text("""
            INSERT INTO video_analyses (
                id, media_asset_id, prompt, status, analysis_result
            )
            VALUES (:id, :media_asset_id, :prompt, 'processing', :analysis_result)
        """),
        {
            "id": analysis_id,
            "media_asset_id": media_asset_id,
            "prompt": prompt,
            "analysis_result": "{}",  # Empty JSON to satisfy NOT NULL
        }
    )
    return analysis_id


async def update_analysis_status(
    conn: AsyncConnection,
    analysis_id: UUID,
    status: str,
    analysis_result: dict | None = None,
    token_usage: int | None = None,
    error: str | None = None,
) -> None:
    """Update analysis status and optionally set result or error."""
    updates = ["status = :status"]
    params = {"analysis_id": analysis_id, "status": status}
    
    if analysis_result is not None:
        updates.append("analysis_result = :analysis_result")
        params["analysis_result"] = json.dumps(analysis_result)
    if token_usage is not None:
        updates.append("token_usage = :token_usage")
        params["token_usage"] = token_usage
    if error is not None:
        updates.append("error = :error")
        params["error"] = error
    
    await conn.execute(
        text(f"""
            UPDATE video_analyses
            SET {', '.join(updates)}
            WHERE id = :analysis_id
        """),
        params
    )


async def insert_video_analysis(
    conn: AsyncConnection,
    media_asset_id: UUID,
    twelvelabs_asset_id: UUID | None,
    prompt: str,
    analysis_result: dict,
    token_usage: int | None = None,
    raw_gcs_uri: str | None = None,
) -> UUID:
    """Insert a completed video analysis result."""
    analysis_id = uuid4()
    await conn.execute(
        text("""
            INSERT INTO video_analyses (
                id, media_asset_id, twelvelabs_asset_id, prompt,
                analysis_result, token_usage, raw_gcs_uri, status
            )
            VALUES (
                :id, :media_asset_id, :twelvelabs_asset_id, :prompt,
                :analysis_result, :token_usage, :raw_gcs_uri, 'completed'
            )
        """),
        {
            "id": analysis_id,
            "media_asset_id": media_asset_id,
            "twelvelabs_asset_id": twelvelabs_asset_id,
            "prompt": prompt,
            "analysis_result": json.dumps(analysis_result),
            "token_usage": token_usage,
            "raw_gcs_uri": raw_gcs_uri,
        }
    )
    return analysis_id
