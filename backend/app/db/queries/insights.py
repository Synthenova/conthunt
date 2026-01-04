"""Database query functions for board insights."""
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing


@log_query_timing
async def get_board_insights(
    conn: AsyncConnection,
    board_id: UUID,
) -> dict | None:
    result = await conn.execute(
        text("""
            SELECT id, board_id, status, insights_result, error,
                   created_at, updated_at, last_completed_at
            FROM board_insights
            WHERE board_id = :board_id
        """),
        {"board_id": board_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "board_id": row[1],
        "status": row[2],
        "insights_result": row[3],
        "error": row[4],
        "created_at": row[5],
        "updated_at": row[6],
        "last_completed_at": row[7],
    }


@log_query_timing
async def upsert_pending_board_insights(
    conn: AsyncConnection,
    board_id: UUID,
) -> UUID:
    """Create or update board insights with 'queued' status (processing starts on pickup)."""
    insights_id = uuid4()
    result = await conn.execute(
        text("""
            INSERT INTO board_insights (
                id, board_id, status, insights_result
            )
            VALUES (
                :id, :board_id, 'queued', :insights_result
            )
            ON CONFLICT (board_id) DO UPDATE
            SET status = 'queued',
                error = NULL,
                updated_at = now()
            RETURNING id
        """),
        {
            "id": insights_id,
            "board_id": board_id,
            "insights_result": "{}",
        }
    )
    return result.scalar_one()


@log_query_timing
async def update_board_insights_status(
    conn: AsyncConnection,
    insights_id: UUID,
    status: str,
    insights_result: Optional[dict] = None,
    error: Optional[str] = None,
    last_completed_at: Optional[datetime] = None,
) -> None:
    updates = ["status = :status", "updated_at = now()"]
    params: dict = {"insights_id": insights_id, "status": status}

    if insights_result is not None:
        updates.append("insights_result = :insights_result")
        params["insights_result"] = json.dumps(insights_result)
    if error is not None:
        updates.append("error = :error")
        params["error"] = error
    if last_completed_at is not None:
        updates.append("last_completed_at = :last_completed_at")
        params["last_completed_at"] = last_completed_at

    await conn.execute(
        text(f"""
            UPDATE board_insights
            SET {', '.join(updates)}
            WHERE id = :insights_id
        """),
        params
    )


@log_query_timing
async def get_board_media_assets_since(
    conn: AsyncConnection,
    board_id: UUID,
    since: Optional[datetime] = None,
) -> List[dict]:
    if since is None:
        result = await conn.execute(
            text("""
                SELECT ma.id, bi.added_at
                FROM board_items bi
                JOIN media_assets ma
                  ON ma.content_item_id = bi.content_item_id
                 AND ma.asset_type = 'video'
                WHERE bi.board_id = :board_id
                ORDER BY bi.added_at DESC
            """),
            {"board_id": board_id}
        )
    else:
        result = await conn.execute(
            text("""
                SELECT ma.id, bi.added_at
                FROM board_items bi
                JOIN media_assets ma
                  ON ma.content_item_id = bi.content_item_id
                 AND ma.asset_type = 'video'
                WHERE bi.board_id = :board_id
                  AND bi.added_at > :since
                ORDER BY bi.added_at DESC
            """),
            {"board_id": board_id, "since": since}
        )
    return [
        {"media_asset_id": row[0], "added_at": row[1]}
        for row in result.fetchall()
    ]


@log_query_timing
async def get_board_insights_progress(
    conn: AsyncConnection,
    board_id: UUID,
) -> dict:
    """Get progress of video analysis for a board (total, analyzed, failed counts)."""
    result = await conn.execute(
        text("""
            SELECT 
                COUNT(DISTINCT ma.id) AS total_videos,
                COUNT(DISTINCT CASE WHEN va.status = 'completed' THEN va.media_asset_id END) AS analyzed_videos,
                COUNT(DISTINCT CASE WHEN va.status = 'failed' THEN va.media_asset_id END) AS failed_videos
            FROM board_items bi
            JOIN media_assets ma
              ON ma.content_item_id = bi.content_item_id
             AND ma.asset_type = 'video'
            LEFT JOIN video_analyses va
              ON va.media_asset_id = ma.id
            WHERE bi.board_id = :board_id
        """),
        {"board_id": board_id}
    )
    row = result.fetchone()
    return {
        "total_videos": row[0] if row else 0,
        "analyzed_videos": row[1] if row else 0,
        "failed_videos": row[2] if row else 0,
    }
