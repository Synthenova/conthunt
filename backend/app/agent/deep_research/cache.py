from __future__ import annotations

from datetime import datetime, timezone

from langchain_core.runnables import RunnableConfig

from app.agent.deep_research import gcs_store
from app.agent.tools import get_video_analysis


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cache_path(media_asset_id: str) -> str:
    return f"analysis/{media_asset_id}.json"


async def get_cached_analysis(chat_id: str, media_asset_id: str) -> str | None:
    payload = await gcs_store.read_json(chat_id, _cache_path(media_asset_id))
    if not isinstance(payload, dict):
        return None
    analysis = payload.get("analysis")
    return str(analysis) if analysis else None


async def set_cached_analysis(chat_id: str, media_asset_id: str, analysis_str: str) -> None:
    await gcs_store.write_json(
        chat_id,
        _cache_path(media_asset_id),
        {
            "media_asset_id": media_asset_id,
            "analysis": analysis_str,
            "cached_at": _now_iso(),
        },
    )


async def ensure_analysis(chat_id: str, media_asset_id: str, config: RunnableConfig) -> str:
    cached = await get_cached_analysis(chat_id, media_asset_id)
    if cached:
        return cached

    tool_result = await get_video_analysis.ainvoke({"media_asset_id": media_asset_id}, config=config)
    analysis = ""
    if isinstance(tool_result, dict):
        if tool_result.get("error"):
            raise RuntimeError(str(tool_result.get("error")))
        analysis = str(tool_result.get("analysis") or "")
    else:
        analysis = str(tool_result or "")

    if not analysis:
        raise RuntimeError("video analysis missing")

    await set_cached_analysis(chat_id, media_asset_id, analysis)
    return analysis

