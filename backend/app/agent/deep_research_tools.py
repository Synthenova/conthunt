"""Tools specific to deep research orchestration."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from app.core.logging import logger
from uuid import UUID

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.model_factory import init_chat_model
from app.agent.tools import _get_api_base_url, _get_headers, get_video_analysis
from app.core import get_settings
from app.llm.context import set_llm_context


def _get_chat_id_from_config(config: RunnableConfig) -> str | None:
    configurable = (config or {}).get("configurable") or {}
    return configurable.get("chat_id")


def _get_user_id_from_config(config: RunnableConfig) -> str | None:
    configurable = (config or {}).get("configurable") or {}
    return configurable.get("user_id")


def _gcs_key_for_chat(chat_id: str, filename: str) -> str:
    return f"deepagents/{chat_id}/{filename}"


async def _read_json_from_gcs(chat_id: str, filename: str) -> dict:
    from google.cloud import storage

    settings = get_settings()
    key = _gcs_key_for_chat(chat_id, filename)

    def _read():
        client = storage.Client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        if not blob.exists():
            return {}
        content = blob.download_as_text()
        return json.loads(content)

    return await asyncio.to_thread(_read)


async def _write_json_to_gcs(chat_id: str, filename: str, payload: dict) -> None:
    from google.cloud import storage

    settings = get_settings()
    key = _gcs_key_for_chat(chat_id, filename)
    data = json.dumps(payload, ensure_ascii=False, indent=2)

    def _write():
        client = storage.Client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        blob.upload_from_string(data.encode("utf-8"), content_type="application/json")

    await asyncio.to_thread(_write)


@tool
async def deep_search_wait(
    query: str,
    config: RunnableConfig,
) -> str:
    """
    Start a search for a single query, wait for completion, then return summary text.
    """
    headers = await _get_headers(config)
    if not headers.get("Authorization"):
        return "Error: Authentication required."

    url = f"{_get_api_base_url()}/search"
    payload = {
        "query": query,
        "inputs": {
            "tiktok_top": {},
            "tiktok_keyword": {},
            "instagram_reels": {},
            "youtube": {},
        },
    }

    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return "Error: chat_id is required."

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        search_id = result.get("search_id")
        if not search_id:
            return "Error: No search_id returned."

    # Wait for completion via SSE, then fetch summary once.
    stream_url = f"{_get_api_base_url()}/search/{search_id}/stream"
    summary_url = f"{_get_api_base_url()}/searches/{search_id}/items/summary"
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", stream_url, headers=headers) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                data = await resp.json()
                if data.get("status") == "failed":
                    return f"Error: Search {search_id} failed."
            else:
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload:
                        continue
                    if '"type": "done"' in payload:
                        break
                    if '"type": "error"' in payload:
                        return f"Error: Search {search_id} failed."

        summary_resp = await client.get(summary_url, headers=headers)
        summary_resp.raise_for_status()
        items = summary_resp.json()

        # Update searches.json with full summary info
        searches = await _read_json_from_gcs(chat_id, "searches.json")
        searches[str(search_id)] = {
            "query": query,
            "summary_items": items,
        }
        await _write_json_to_gcs(chat_id, "searches.json", searches)

        unique_ids = len({i.get("media_asset_id") for i in items if i.get("media_asset_id")})
        return (
            "searches written to searches.json\n"
            f"search_id: {search_id}\n"
            f"count: {len(items)}\n"
            f"unique_media_asset_ids: {unique_ids}"
        )


@tool
async def deep_analyze_batch_with_criteria(
    criteria: str,
    config: RunnableConfig,
) -> str:
    """
    Analyze the next batch of 25 videos (sorted by views) and write justifications.
    """
    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return "Error: chat_id is required."

    scores = await _read_json_from_gcs(chat_id, "scores.json")
    if scores:
        high = [v for v in scores.values() if v >= 0.9]
        if len(high) >= 50:
            return f"Enough >=0.9 scores already present. Stop. count_ge_0.9: {len(high)}"

    searches = await _read_json_from_gcs(chat_id, "searches.json")
    if not searches:
        return "Error: searches.json not found or empty."

    # Flatten and dedup
    items = []
    for entry in searches.values():
        items.extend(entry.get("summary_items") or [])

    seen = set()
    deduped = []
    for item in items:
        mid = item.get("media_asset_id")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        deduped.append(item)

    def _views(item: dict) -> int:
        metrics = item.get("metrics") or {}
        return int(metrics.get("view_count") or 0)

    deduped.sort(key=_views, reverse=True)

    justifications = await _read_json_from_gcs(chat_id, "analysis_justifications.json")
    done_ids = set(justifications.keys())

    settings = get_settings()
    batch_size = max(1, settings.DEEP_RESEARCH_BATCH_SIZE)

    # Next batch
    batch = [i for i in deduped if i.get("media_asset_id") not in done_ids][:batch_size]
    if not batch:
        return "No remaining videos to analyze."

    db_concurrency = max(1, settings.DEEP_RESEARCH_DB_CONCURRENCY)
    db_sem = asyncio.Semaphore(db_concurrency)

    base_config = config or {}
    configurable = base_config.get("configurable") or {}
    filters = dict(configurable.get("filters") or {})
    filters["deep_research_enabled"] = True
    deep_research_config = {
        **base_config,
        "configurable": {
            **configurable,
            "filters": filters,
        },
    }

    async def _analyze_one(media_asset_id: str) -> tuple[str, str]:
        try:
            async with db_sem:
                tool_result = await asyncio.wait_for(
                    get_video_analysis.ainvoke(
                        {"media_asset_id": media_asset_id},
                        config=deep_research_config,
                    ),
                    timeout=120.0,  # 2 minute timeout for video analysis
                )
        except asyncio.TimeoutError:
            logger.warning("[deep_research] get_video_analysis timed out for %s", media_asset_id)
            return media_asset_id, "Analysis timed out."
        except Exception:
            logger.exception("[deep_research] get_video_analysis failed for %s", media_asset_id)
            return media_asset_id, "Analysis failed due to error."

        if isinstance(tool_result, dict) and tool_result.get("error"):
            error_msg = str(tool_result.get("error"))
            if "Video download failed" in error_msg:
                logger.warning("[deep_research] Video download failed for %s", media_asset_id)
                return media_asset_id, "Invalid video (download failed)."
            logger.warning("[deep_research] Error for %s: %s", media_asset_id, error_msg)
            return media_asset_id, f"Analysis error: {error_msg}"

        analysis = tool_result.get("analysis")
        if not analysis:
            logger.warning("[deep_research] Analysis missing for %s", media_asset_id)
            return media_asset_id, "Analysis missing or still processing."

        try:
            model = init_chat_model("openrouter/google/gemini-3-flash-preview", temperature=0.2)
            system = SystemMessage(content="Describe the video and explain why it does or does not meet the criteria in 1-2 sentences.")
            human = HumanMessage(content=f"""
Criteria:
{criteria}

Analysis:
{tool_result}
""".strip())
            with set_llm_context(user_id=_get_user_id_from_config(config), route="deep_research.justify"):
                resp = await asyncio.wait_for(
                    model.ainvoke([system, human]),
                    timeout=60.0,  # 1 minute timeout for LLM justification
                )
            return media_asset_id, str(resp.content).strip()
        except asyncio.TimeoutError:
            logger.warning("[deep_research] LLM justification timed out for %s", media_asset_id)
            return media_asset_id, "Justification timed out."
        except Exception:
            logger.exception("[deep_research] LLM justification failed for %s", media_asset_id)
            return media_asset_id, "Justification failed."

    results_raw = await asyncio.gather(
        *[_analyze_one(i.get("media_asset_id")) for i in batch],
        return_exceptions=True,
    )

    # Filter out exceptions (shouldn't happen now, but safety net)
    results = []
    for i, r in enumerate(results_raw):
        if isinstance(r, Exception):
            mid = batch[i].get("media_asset_id")
            logger.exception("[deep_research] Unexpected exception for %s: %s", mid, r)
            results.append((mid, "Unexpected error during analysis."))
        else:
            results.append(r)

    for mid, justification in results:
        justifications[mid] = {
            "justification": justification,
        }

    await _write_json_to_gcs(chat_id, "analysis_justifications.json", justifications)

    justification_lines = []
    for mid, justification in results:
        justification_lines.append(f"{mid}\njustification: {justification}\n")

    return (
        f"analyzed: {len(results)}\n"
        f"total_analyzed: {len(justifications)}\n"
        "justifications written to analysis_justifications.json\n\n"
        "justifications:\n"
        + "\n".join(justification_lines).strip()
    )


@tool
async def write_scores_and_stats(
    scores: Dict[str, float],
    config: RunnableConfig,
) -> str:
    """
    Persist scores.json and return stats (>=0.9, needed to reach 50).
    """
    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return "Error: chat_id is required."

    await _write_json_to_gcs(chat_id, "scores.json", scores)
    high = [v for v in scores.values() if v >= 0.9]
    needed = max(0, 50 - len(high))
    return f"scores written to scores.json\n>=0.9: {len(high)}\nneeded_to_50: {needed}"


@tool
async def create_final_report(config: RunnableConfig) -> Dict[str, Any]:
    """
    Build top 30 report from scores.json and analysis_justifications.json.
    Returns ids + scores + justifications for orchestrator use.
    """
    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return {"error": "chat_id is required"}

    scores = await _read_json_from_gcs(chat_id, "scores.json")
    justifications = await _read_json_from_gcs(chat_id, "analysis_justifications.json")

    if not scores:
        return {"error": "scores.json missing or empty"}
    if not justifications:
        return {"error": "analysis_justifications.json missing or empty"}

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:30]

    results = []
    for media_id, score in top:
        info = justifications.get(media_id) or {}
        results.append({
            "media_asset_id": media_id,
            "score": score,
            "summary": info.get("summary") or "",
            "justification": info.get("justification") or "",
        })

    return {
        "count": len(results),
        "results": results,
    }
