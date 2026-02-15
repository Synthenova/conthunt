from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from firebase_admin import auth as firebase_auth

from app.agent.deep_research import gcs_store
from app.agent.tools import get_video_analysis
from app.auth.firebase import init_firebase
from app.core import get_settings
from app.core.logging import logger
from app.db import set_rls_user
from app.db.queries.analysis import get_video_analyses_by_media_assets
from app.db.session import get_db_connection
from app.services.analysis_service import analysis_service

settings = get_settings()
_DEEP_CACHE_IO_CONCURRENCY = 100


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cache_path(media_asset_id: str) -> str:
    return f"analysis/{media_asset_id}.json"


async def get_cached_analysis(chat_id: str, media_asset_id: str) -> str | None:
    payload = await gcs_store.read_json(chat_id, _cache_path(media_asset_id))
    if not isinstance(payload, dict):
        logger.info("[DEEP_CACHE] MISS media_asset=%s (no cached file)", media_asset_id)
        return None
    analysis = payload.get("analysis")
    if analysis:
        logger.info("[DEEP_CACHE] HIT media_asset=%s", media_asset_id)
    return str(analysis) if analysis else None


async def set_cached_analysis(chat_id: str, media_asset_id: str, analysis_str: str) -> None:
    logger.info("[DEEP_CACHE] WRITING media_asset=%s len=%d", media_asset_id, len(analysis_str))
    await gcs_store.write_json(
        chat_id,
        _cache_path(media_asset_id),
        {
            "media_asset_id": media_asset_id,
            "analysis": analysis_str,
            "cached_at": _now_iso(),
        },
    )
    logger.info("[DEEP_CACHE] WRITTEN media_asset=%s path=%s", media_asset_id, _cache_path(media_asset_id))


async def ensure_analysis(chat_id: str, media_asset_id: str, config: RunnableConfig) -> str:
    logger.info("[DEEP_CACHE] ensure_analysis START media_asset=%s", media_asset_id)
    cached = await get_cached_analysis(chat_id, media_asset_id)
    if cached:
        logger.info("[DEEP_CACHE] ensure_analysis CACHED media_asset=%s", media_asset_id)
        return cached

    logger.info("[DEEP_CACHE] ensure_analysis FETCHING media_asset=%s (calling get_video_analysis)", media_asset_id)
    tool_result = await get_video_analysis.ainvoke({"media_asset_id": media_asset_id}, config=config)
    analysis = ""
    if isinstance(tool_result, dict):
        if tool_result.get("error"):
            logger.error("[DEEP_CACHE] ensure_analysis ERROR media_asset=%s error=%s", media_asset_id, tool_result.get("error"))
            raise RuntimeError(str(tool_result.get("error")))
        analysis = str(tool_result.get("analysis") or "")
    else:
        analysis = str(tool_result or "")

    if not analysis:
        logger.error("[DEEP_CACHE] ensure_analysis EMPTY media_asset=%s", media_asset_id)
        raise RuntimeError("video analysis missing")

    logger.info("[DEEP_CACHE] ensure_analysis SAVING media_asset=%s analysis_len=%d", media_asset_id, len(analysis))
    await set_cached_analysis(chat_id, media_asset_id, analysis)
    return analysis


async def ensure_analyses_batch(
    chat_id: str,
    media_asset_ids: list[str],
    config: RunnableConfig,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Ensure analyses exist for many media_asset_ids at once.

    Returns:
      (analysis_by_media_asset_id, error_by_media_asset_id)
    """
    deduped_ids = list(dict.fromkeys([mid for mid in media_asset_ids if mid]))
    if not deduped_ids:
        return {}, {}

    read_sem = asyncio.Semaphore(_DEEP_CACHE_IO_CONCURRENCY)

    async def _read_one(media_asset_id: str) -> tuple[str, str | None]:
        async with read_sem:
            cached = await get_cached_analysis(chat_id, media_asset_id)
        return media_asset_id, cached

    cached_by_id: dict[str, str] = {}
    missing_ids: list[str] = []
    for media_asset_id, cached in await asyncio.gather(*(_read_one(mid) for mid in deduped_ids)):
        if cached:
            cached_by_id[media_asset_id] = cached
        else:
            missing_ids.append(media_asset_id)

    if not missing_ids:
        return cached_by_id, {}

    configurable = config.get("configurable", {}) if config else {}
    auth_token = configurable.get("x-auth-token")
    if not auth_token:
        return cached_by_id, {mid: "Authentication required. Please provide x-auth-token." for mid in missing_ids}

    db_user_id: UUID | None = None
    user_role = "free"
    try:
        init_firebase()
        decoded = firebase_auth.verify_id_token(auth_token)
        user_role = decoded.get("role", "free")
        db_user_id_str = decoded.get("db_user_id")
        if db_user_id_str:
            db_user_id = UUID(db_user_id_str)
    except Exception:
        logger.exception("[DEEP_CACHE] token verification failed for batch ensure")

    if not db_user_id:
        return cached_by_id, {mid: "Session expired. Please log out and log back in." for mid in missing_ids}

    missing_uuids: list[UUID] = []
    parse_errors: dict[str, str] = {}
    for media_asset_id in missing_ids:
        try:
            missing_uuids.append(UUID(media_asset_id))
        except ValueError:
            parse_errors[media_asset_id] = "Invalid media_asset_id format."

    valid_missing_ids = [mid for mid in missing_ids if mid not in parse_errors]
    if not valid_missing_ids:
        return cached_by_id, parse_errors

    batch_result = await analysis_service.trigger_paid_analysis_batch(
        user_id=db_user_id,
        user_role=user_role,
        media_asset_ids=[UUID(mid) for mid in valid_missing_ids],
        background_tasks=None,
        context_source="deep_research_batch",
        record_streak=False,
        chat_id=chat_id,
    )
    response_by_asset = batch_result.get("responses", {}) if isinstance(batch_result, dict) else {}
    early_errors: dict[str, str] = {}
    for asset_id in valid_missing_ids:
        response = response_by_asset.get(asset_id) if isinstance(response_by_asset, dict) else None
        if isinstance(response, dict) and response.get("error") and response.get("status") == "failed":
            early_errors[asset_id] = str(response.get("error"))

    poll_timeout_s = float(getattr(settings, "DEEP_RESEARCH_ANALYSIS_POLL_TIMEOUT_S", 240.0))
    first_delay_s = float(getattr(settings, "DEEP_RESEARCH_ANALYSIS_POLL_FIRST_DELAY_S", 30.0))
    interval_s = float(getattr(settings, "DEEP_RESEARCH_ANALYSIS_POLL_INTERVAL_S", 5.0))
    wait_ids = [UUID(mid) for mid in valid_missing_ids if mid not in early_errors]

    if wait_ids:
        await asyncio.sleep(max(0.0, first_delay_s))
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(1.0, poll_timeout_s)
        pending_ids = set(wait_ids)
        write_sem = asyncio.Semaphore(_DEEP_CACHE_IO_CONCURRENCY)

        async def _write_cache(media_asset_id: str, analysis: str) -> None:
            async with write_sem:
                await set_cached_analysis(chat_id, media_asset_id, analysis)

        while pending_ids and loop.time() < deadline:
            async with get_db_connection() as conn:
                await set_rls_user(conn, db_user_id)
                rows = await get_video_analyses_by_media_assets(conn, list(pending_ids))
                await conn.commit()
            rows_by_asset = {row["media_asset_id"]: row for row in rows}
            completed_now: list[UUID] = []
            cache_writes: list[asyncio.Task] = []
            for media_asset_uuid in list(pending_ids):
                row = rows_by_asset.get(media_asset_uuid)
                if not row:
                    continue
                status = row.get("status", "")
                if status == "completed" and isinstance(row.get("analysis_result"), dict):
                    analysis = row["analysis_result"].get("analysis") or ""
                    if analysis:
                        media_asset_id = str(media_asset_uuid)
                        cached_by_id[media_asset_id] = str(analysis)
                        cache_writes.append(asyncio.create_task(_write_cache(media_asset_id, str(analysis))))
                    completed_now.append(media_asset_uuid)
                elif status == "failed":
                    early_errors[str(media_asset_uuid)] = str(row.get("error") or "Analysis failed")
                    completed_now.append(media_asset_uuid)
            if cache_writes:
                await asyncio.gather(*cache_writes)
            for media_asset_uuid in completed_now:
                pending_ids.discard(media_asset_uuid)
            if pending_ids:
                await asyncio.sleep(max(0.0, interval_s))

        for media_asset_uuid in pending_ids:
            early_errors[str(media_asset_uuid)] = "Analysis is still processing. Please try again in a moment."

    early_errors.update(parse_errors)
    return cached_by_id, early_errors
