from __future__ import annotations

import logging
from datetime import datetime, timezone

from langchain_core.runnables import RunnableConfig

from app.agent.deep_research import gcs_store
from app.agent.tools import get_video_analysis
from app.core.logging import logger


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

