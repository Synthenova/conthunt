"""Database query functions for video analysis (Gemini-based)."""
import json
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing
from app.core import get_settings



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



async def get_video_analyses_by_media_assets(
    conn: AsyncConnection,
    media_asset_ids: list[UUID],
) -> list[dict]:
    """Get cached video analyses for a list of media assets."""
    if not media_asset_ids:
        return []
    result = await conn.execute(
        text("""
            SELECT id, media_asset_id, twelvelabs_asset_id, prompt,
                   analysis_result, token_usage, created_at, status, error
            FROM video_analyses
            WHERE media_asset_id = ANY(:media_asset_ids)
        """),
        {"media_asset_ids": media_asset_ids}
    )
    rows = result.fetchall()
    return [
        {
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
        for row in rows
    ]



async def claim_or_create_analysis(
    conn: AsyncConnection,
    media_asset_id: UUID,
    prompt: str,
) -> tuple[UUID, str, datetime, bool]:
    """
    Atomically claim or create an analysis record.
    
    Returns:
        Tuple of (analysis_id, status, created_at, was_created)
    """
    analysis_id = uuid4()
    result = await conn.execute(
        text("""
            WITH inserted AS (
                INSERT INTO video_analyses (
                    id, media_asset_id, prompt, status, analysis_result
                )
                VALUES (:id, :media_asset_id, :prompt, 'queued', :analysis_result)
                ON CONFLICT (media_asset_id) DO NOTHING
                RETURNING id, status, created_at, TRUE AS was_inserted
            )
            SELECT id, status, created_at, was_inserted
            FROM inserted
            UNION ALL
            SELECT va.id, va.status, va.created_at, FALSE AS was_inserted
            FROM video_analyses va
            WHERE va.media_asset_id = :media_asset_id
              AND NOT EXISTS (SELECT 1 FROM inserted)
            LIMIT 1
        """),
        {
            "id": analysis_id,
            "media_asset_id": media_asset_id,
            "prompt": prompt,
            "analysis_result": "{}",
        }
    )
    row = result.fetchone()
    if not row:
        raise RuntimeError("claim_or_create_analysis: failed to fetch analysis row")
    return (row[0], row[1], row[2], row[3])


async def claim_or_create_analyses_batch(
    conn: AsyncConnection,
    media_asset_ids: list[UUID],
    prompt: str,
) -> dict[UUID, dict[str, Any]]:
    """
    Batch variant of claim_or_create_analysis.

    Returns:
        {media_asset_id: {"analysis_id": UUID, "status": str, "created_at": datetime, "was_created": bool}}
    """
    if not media_asset_ids:
        return {}

    # Deduplicate while preserving stable order
    deduped_ids = list(dict.fromkeys(media_asset_ids))
    payload = [
        {
            "id": str(uuid4()),
            "media_asset_id": str(media_asset_id),
            "prompt": prompt,
            "analysis_result": "{}",
        }
        for media_asset_id in deduped_ids
    ]

    inserted_result = await conn.execute(
        text(
            """
            INSERT INTO video_analyses (
                id, media_asset_id, prompt, status, analysis_result
            )
            SELECT
                x.id, x.media_asset_id, x.prompt, 'queued', x.analysis_result::jsonb
            FROM jsonb_to_recordset(CAST(:payload AS jsonb)) AS x(
                id uuid, media_asset_id uuid, prompt text, analysis_result text
            )
            ON CONFLICT (media_asset_id) DO NOTHING
            RETURNING media_asset_id
            """
        ),
        {"payload": json.dumps(payload)},
    )
    inserted_media_asset_ids = {row[0] for row in inserted_result.fetchall()}

    rows_result = await conn.execute(
        text(
            """
            SELECT id, media_asset_id, status, created_at
            FROM video_analyses
            WHERE media_asset_id = ANY(:media_asset_ids)
            """
        ),
        {"media_asset_ids": deduped_ids},
    )

    out: dict[UUID, dict[str, Any]] = {}
    for row in rows_result.fetchall():
        media_asset_id = row[1]
        out[media_asset_id] = {
            "analysis_id": row[0],
            "status": row[2],
            "created_at": row[3],
            "was_created": media_asset_id in inserted_media_asset_ids,
        }
    return out


async def rescue_stale_or_failed_analyses_batch(
    conn: AsyncConnection,
    analyses: list[dict[str, Any]],
    stale_after_seconds: int = 600,
) -> set[UUID]:
    """
    Reset stale/failed analyses to queued in one update.
    """
    if not analyses:
        return set()

    now_utc = datetime.utcnow()
    to_rescue: list[UUID] = []
    for row in analyses:
        status = row.get("status")
        created_at = row.get("created_at")
        should_rescue = status == "failed"

        if not should_rescue and status in ("queued", "processing") and created_at:
            cmp_now = datetime.utcnow()
            try:
                if created_at.tzinfo is not None:
                    cmp_now = datetime.now(created_at.tzinfo)
            except Exception:
                cmp_now = now_utc
            if (cmp_now - created_at).total_seconds() > stale_after_seconds:
                should_rescue = True

        if should_rescue and row.get("analysis_id"):
            to_rescue.append(row["analysis_id"])

    if not to_rescue:
        return set()

    await conn.execute(
        text(
            """
            UPDATE video_analyses
            SET status = 'queued',
                created_at = :now_utc,
                error = NULL
            WHERE id = ANY(:analysis_ids)
            """
        ),
        {"analysis_ids": to_rescue, "now_utc": now_utc},
    )
    return set(to_rescue)


async def update_analysis_status_processing_batch(
    conn: AsyncConnection,
    analysis_ids: list[UUID],
) -> None:
    if not analysis_ids:
        return
    await conn.execute(
        text(
            """
            UPDATE video_analyses
            SET status = 'processing'
            WHERE id = ANY(:analysis_ids)
            """
        ),
        {"analysis_ids": analysis_ids},
    )


async def update_analysis_status_completed_batch(
    conn: AsyncConnection,
    completed_rows: list[dict[str, Any]],
) -> None:
    """
    completed_rows format:
      [{"analysis_id": UUID, "analysis": str}, ...]
    """
    if not completed_rows:
        return

    payload = [
        {
            "analysis_id": str(row["analysis_id"]),
            "analysis_result": json.dumps({"analysis": row["analysis"]}),
        }
        for row in completed_rows
    ]
    await conn.execute(
        text(
            """
            UPDATE video_analyses va
            SET status = 'completed',
                analysis_result = x.analysis_result::jsonb,
                error = NULL
            FROM jsonb_to_recordset(CAST(:payload AS jsonb)) AS x(
                analysis_id uuid, analysis_result text
            )
            WHERE va.id = x.analysis_id
            """
        ),
        {"payload": json.dumps(payload)},
    )


async def update_analysis_status_failed_batch(
    conn: AsyncConnection,
    failed_rows: list[dict[str, Any]],
) -> None:
    """
    failed_rows format:
      [{"analysis_id": UUID, "error": str}, ...]
    """
    if not failed_rows:
        return

    payload = [
        {
            "analysis_id": str(row["analysis_id"]),
            "error": (str(row.get("error") or "Analysis failed"))[:1000],
        }
        for row in failed_rows
    ]
    await conn.execute(
        text(
            """
            UPDATE video_analyses va
            SET status = 'failed',
                error = x.error
            FROM jsonb_to_recordset(CAST(:payload AS jsonb)) AS x(
                analysis_id uuid, error text
            )
            WHERE va.id = x.analysis_id
            """
        ),
        {"payload": json.dumps(payload)},
    )


async def update_analysis_status_queued_batch(
    conn: AsyncConnection,
    analysis_ids: list[UUID],
) -> None:
    if not analysis_ids:
        return
    await conn.execute(
        text(
            """
            UPDATE video_analyses
            SET status = 'queued',
                error = NULL
            WHERE id = ANY(:analysis_ids)
            """
        ),
        {"analysis_ids": analysis_ids},
    )



async def update_analysis_status(
    conn: AsyncConnection,
    analysis_id: UUID,
    status: str,
    analysis_result: dict | None = None,
    token_usage: int | None = None,
    error: str | None = None,
    created_at: datetime | None = None,
    step_or_attempt: str | int = "0",
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
    if created_at is not None:
        updates.append("created_at = :created_at")
        params["created_at"] = created_at
    
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



async def has_user_accessed_analysis(
    conn: AsyncConnection,
    user_id: UUID,
    media_asset_id: UUID,
) -> bool:
    """Check if user has already been charged for this analysis."""
    result = await conn.execute(
        text("""
            SELECT 1 FROM user_analysis_access
            WHERE user_id = :user_id AND media_asset_id = :media_asset_id
            LIMIT 1
        """),
        {"user_id": user_id, "media_asset_id": media_asset_id}
    )
    return result.fetchone() is not None



async def record_user_analysis_access(
    conn: AsyncConnection,
    user_id: UUID,
    media_asset_id: UUID,
) -> None:
    """Record that user accessed this analysis (idempotent via ON CONFLICT)."""
    await conn.execute(
        text("""
            INSERT INTO user_analysis_access (user_id, media_asset_id)
            VALUES (:user_id, :media_asset_id)
            ON CONFLICT (user_id, media_asset_id) DO NOTHING
        """),
        {"user_id": user_id, "media_asset_id": media_asset_id}
    )
