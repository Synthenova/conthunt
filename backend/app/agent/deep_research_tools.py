"""Tools specific to deep research orchestration."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.tools import _get_api_base_url, _get_headers
from app.core import get_settings
from app.core.logging import logger

settings = get_settings()

from app.agent.deep_research.tools_analysis import (
    analyze_search_batch_with_criteria,
    answer_video_question,
)


def _get_chat_id_from_config(config: RunnableConfig) -> str | None:
    configurable = (config or {}).get("configurable") or {}
    return configurable.get("chat_id")


def _gcs_key_for_chat(chat_id: str, filename: str) -> str:
    return f"deepagents/{chat_id}/{filename}"


async def _read_json_from_gcs(chat_id: str, filename: str) -> dict:
    from google.cloud import storage

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

    key = _gcs_key_for_chat(chat_id, filename)
    data = json.dumps(payload, ensure_ascii=False, indent=2)

    def _write():
        client = storage.Client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        blob.upload_from_string(data.encode("utf-8"), content_type="application/json")

    await asyncio.to_thread(_write)

async def _read_text_from_gcs(chat_id: str, filename: str) -> str:
    from google.cloud import storage

    key = _gcs_key_for_chat(chat_id, filename)

    def _read() -> str:
        client = storage.Client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        if not blob.exists():
            return ""
        return blob.download_as_text()

    return await asyncio.to_thread(_read)


async def _write_text_to_gcs(chat_id: str, filename: str, content: str, *, content_type: str) -> None:
    from google.cloud import storage

    key = _gcs_key_for_chat(chat_id, filename)

    def _write() -> None:
        client = storage.Client()
        bucket = client.bucket(settings.GCS_DEEPAGNT_FS)
        blob = bucket.blob(key)
        blob.upload_from_string(content.encode("utf-8"), content_type=content_type)

    await asyncio.to_thread(_write)


async def _append_jsonl_to_gcs(chat_id: str, filename: str, record: dict) -> None:
    # Simple implementation: read + append + write. Good enough for now.
    existing = await _read_text_from_gcs(chat_id, filename)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    needs_nl = bool(existing) and (not existing.endswith("\n"))
    prefix = "\n" if needs_nl else ""
    content = f"{existing}{prefix}{line}\n"
    await _write_text_to_gcs(chat_id, filename, content, content_type="application/x-ndjson")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_query(q: str) -> str:
    return " ".join((q or "").strip().split())


def _unique_media_asset_ids(items: Iterable[dict]) -> int:
    return len({i.get("media_asset_id") for i in items if i.get("media_asset_id")})


async def _wait_search_done(search_id: str, headers: Dict[str, str]) -> None:
    stream_url = f"{_get_api_base_url()}/search/{search_id}/stream"
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", stream_url, headers=headers) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                data = await resp.json()
                if data.get("status") == "failed":
                    raise RuntimeError(f"Search {search_id} failed.")
                return

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload:
                    continue
                if '"type": "done"' in payload:
                    return
                if '"type": "error"' in payload:
                    raise RuntimeError(f"Search {search_id} failed.")


async def _fetch_search_items_summary(search_id: str, headers: Dict[str, str]) -> List[dict]:
    summary_url = f"{_get_api_base_url()}/searches/{search_id}/items/summary"
    async with httpx.AsyncClient(timeout=30.0) as client:
        summary_resp = await client.get(summary_url, headers=headers)
        summary_resp.raise_for_status()
        items = summary_resp.json()
        return items if isinstance(items, list) else []


async def _run_one_search(query: str, headers: Dict[str, str]) -> Tuple[str, List[dict]]:
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

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        search_id = result.get("search_id")
        if not search_id:
            raise RuntimeError("No search_id returned.")

    await _wait_search_done(str(search_id), headers)
    items = await _fetch_search_items_summary(str(search_id), headers)
    return str(search_id), items


async def _read_progress(chat_id: str) -> dict:
    progress = await _read_json_from_gcs(chat_id, "progress.json")
    if not isinstance(progress, dict):
        progress = {}
    progress.setdefault("search_order", [])
    progress.setdefault("searches", {})
    progress.setdefault("errors_recent", [])
    return progress


async def _write_progress(chat_id: str, progress: dict) -> None:
    progress["last_updated_at"] = _now_iso()
    await _write_json_to_gcs(chat_id, "progress.json", progress)


async def _record_error(progress: dict, query: str, error: str) -> None:
    errors = progress.get("errors_recent") or []
    errors.append({"ts": _now_iso(), "query": query, "error": error})
    progress["errors_recent"] = errors[-20:]


@tool
async def deep_search_batch_wait(
    queries: list[str],
    config: RunnableConfig,
) -> dict:
    """
    Run multiple searches in parallel (capped by DEEP_RESEARCH_SEARCH_CONCURRENCY), wait for completion,
    persist progress + per-search detail files, and return a structured summary.
    """
    headers = await _get_headers(config)
    if not headers.get("Authorization"):
        return {"error": "Authentication required."}

    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return {"error": "chat_id is required."}

    progress = await _read_progress(chat_id)
    searches_index = await _read_json_from_gcs(chat_id, "searches.json")
    if not isinstance(searches_index, dict):
        searches_index = {}

    normalized_to_query: Dict[str, str] = {}
    for q in (queries or []):
        nq = _normalize_query(q)
        if not nq:
            continue
        if nq in normalized_to_query:
            continue
        normalized_to_query[nq] = nq

    sem = asyncio.Semaphore(settings.DEEP_RESEARCH_SEARCH_CONCURRENCY)

    executed: List[dict] = []
    failed: List[dict] = []

    async def _worker(nq: str) -> None:
        try:
            async with sem:
                search_id, items = await _run_one_search(nq, headers)

            fetched_at = _now_iso()
            detail_filename = f"search_{search_id}_detail.json"
            await _write_json_to_gcs(
                chat_id,
                detail_filename,
                {
                    "search_id": search_id,
                    "query": nq,
                    "fetched_at": fetched_at,
                    "summary_items": items,
                },
            )

            count = len(items)
            unique_ids = _unique_media_asset_ids(items)
            created_at = fetched_at

            searches_index[str(search_id)] = {
                "query": nq,
                "created_at": created_at,
                "count": count,
                "unique_media_asset_ids": unique_ids,
                "detail_file": detail_filename,
            }

            # progress.json: concise ground truth
            if str(search_id) not in progress["searches"]:
                progress["search_order"].append(str(search_id))
            progress["searches"][str(search_id)] = {
                "query": nq,
                "created_at": created_at,
                "count": count,
                "unique_media_asset_ids": unique_ids,
                "analyzed_count": 0,
                "unanalyzed_count": unique_ids,
            }

            executed.append(
                {
                    "query": nq,
                    "search_id": str(search_id),
                    "count": count,
                    "unique_media_asset_ids": unique_ids,
                }
            )
        except Exception as e:
            msg = str(e)
            failed.append({"query": nq, "error": msg})
            await _record_error(progress, nq, msg)

    await asyncio.gather(*[_worker(nq) for nq in normalized_to_query.values()])

    await _write_json_to_gcs(chat_id, "searches.json", searches_index)
    await _write_progress(chat_id, progress)

    tool_output = {
        "executed": executed,
        "failed": failed,
        "concurrency": settings.DEEP_RESEARCH_SEARCH_CONCURRENCY,
    }

    await _append_jsonl_to_gcs(
        chat_id,
        "tool_calls.jsonl",
        {
            "ts": _now_iso(),
            "tool": "deep_search_batch_wait",
            "input": {"queries": queries or []},
            "output": tool_output,
            "writes": ["progress.json", "searches.json"],
        },
    )

    return tool_output


@tool
async def get_search_overview(
    search_id: str,
    config: RunnableConfig,
    limit: int = 50,
) -> dict:
    """
    Read a stored per-search detail file and return a compact overview (titles + key metrics).
    """
    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return {"error": "chat_id is required."}

    searches_index = await _read_json_from_gcs(chat_id, "searches.json")
    if not isinstance(searches_index, dict):
        searches_index = {}

    entry = searches_index.get(str(search_id)) or {}
    detail_file = entry.get("detail_file") or f"search_{search_id}_detail.json"

    detail = await _read_json_from_gcs(chat_id, detail_file)
    if not detail:
        return {"error": f"Search detail not found for {search_id}"}

    query = detail.get("query") or entry.get("query") or ""
    items = detail.get("summary_items") or []
    if not isinstance(items, list):
        items = []

    def _views(it: dict) -> int:
        metrics = it.get("metrics") or {}
        try:
            return int(metrics.get("view_count") or 0)
        except Exception:
            return 0

    items_sorted = sorted(items, key=_views, reverse=True)
    slim = []
    for it in items_sorted[: max(0, int(limit or 0))]:
        metrics = it.get("metrics") or {}
        slim.append(
            {
                "media_asset_id": it.get("media_asset_id"),
                "title": it.get("title"),
                "platform": it.get("platform"),
                "creator_handle": it.get("creator_handle"),
                "published_at": it.get("published_at"),
                "view_count": metrics.get("view_count"),
                "like_count": metrics.get("like_count"),
            }
        )

    return {
        "search_id": str(search_id),
        "query": query,
        "count": len(items),
        "items": slim,
    }
