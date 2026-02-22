"""Tools specific to deep research orchestration."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.model_factory import init_chat_model
from app.agent.tools import _get_api_base_url, _get_headers
from app.core import get_settings
from app.core.logging import logger

settings = get_settings()


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


def _safe_int(val) -> int:
    """Convert a value to int, returning 0 on any failure."""
    try:
        return int(val or 0)
    except Exception:
        return 0


@tool
async def web_search(
    query: str,
    config: RunnableConfig,
) -> dict:
    """Run grounded web search and return concise results for search planning."""
    q = (query or "").strip()
    if not q:
        return {"error": "query is required"}

    today_utc = datetime.now(timezone.utc).date().isoformat()
    model = init_chat_model("openrouter/x-ai/grok-4.1-fast:online", temperature=0.2)

    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    f"Current UTC date: {today_utc}. "
                    "Use online web access to gather current web signals. "
                    "Return concise findings relevant to the query."
                )
            ),
            HumanMessage(content=q),
        ]
    )

    return {
        "query": q,
        "content": getattr(response, "content", response),
        "tool_calls": getattr(response, "tool_calls", None) or [],
        "metadata": getattr(response, "additional_kwargs", {}) or {},
    }





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
    Run multiple searches in parallel, wait for completion,
    persist progress + per-search detail files, and return a structured summary.

    Writes two versions of each search result:
      - /searches_raw/search_N.json  (full data with UUIDs — agent-blocked)
      - /searches/search_N.json      (slim, no UUIDs, already ranked by views desc)
    """
    headers = await _get_headers(config)
    if not headers.get("Authorization"):
        return {"error": "Authentication required."}

    chat_id = _get_chat_id_from_config(config)
    if not chat_id:
        return {"error": "chat_id is required."}

    from app.agent.deep_research.progress import (
        read_progress as _read_prog,
        write_progress as _write_prog,
        get_next_search_number,
        register_search,
    )

    progress = await _read_prog(chat_id)

    # Deduplicate + normalize queries
    unique_queries: list[str] = []
    seen: set[str] = set()
    for q in (queries or []):
        nq = _normalize_query(q)
        if not nq or nq in seen:
            continue
        seen.add(nq)
        unique_queries.append(nq)

    if len(unique_queries) < 1:
        return {
            "error": "At least 1 query is required.",
            "status": "invalid_query_count",
            "query_count": len(unique_queries),
            "allowed_range": {"min": 1, "max": 7},
        }
    if len(unique_queries) > 7:
        return {
            "error": "Too many queries. Maximum allowed is 7.",
            "status": "invalid_query_count",
            "query_count": len(unique_queries),
            "allowed_range": {"min": 1, "max": 7},
        }

    # Pre-assign search numbers (sequential, before parallel execution)
    start_num = get_next_search_number(progress)
    query_numbers: dict[str, int] = {}
    for i, nq in enumerate(unique_queries):
        query_numbers[nq] = start_num + i
    progress["next_search_number"] = start_num + len(unique_queries)

    executed: List[dict] = []
    failed: List[dict] = []
    files_written: List[str] = []

    async def _worker(nq: str) -> None:
        search_number = query_numbers[nq]
        try:
            search_id, items = await _run_one_search(nq, headers)

            fetched_at = _now_iso()
            count = len(items)

            # ── Build raw item list (full) + ranked slim list (lean) ─
            raw_items: list[dict] = []
            slim_with_views: list[dict] = []
            for idx, it in enumerate(items, start=1):
                metrics = it.get("metrics") or {}
                view_count = _safe_int(metrics.get("view_count"))
                raw_items.append({
                    "video_id": idx,
                    "media_asset_id": it.get("media_asset_id"),
                    "title": it.get("title") or "",
                    "platform": it.get("platform") or "",
                    "creator_handle": it.get("creator_handle") or "",
                    "published_at": it.get("published_at"),
                    "metrics": metrics,
                    "caption": it.get("primary_text") or it.get("caption") or "",
                    "hashtags": it.get("hashtags") or [],
                })
                slim_with_views.append({
                    "id": idx,
                    "title": it.get("title") or "",
                    "caption": it.get("primary_text") or it.get("caption") or "",
                    "hashtags": it.get("hashtags") or [],
                    "_views": view_count,  # internal ranking key only; removed before writing
                })

            # Deterministic ranking at tool level: highest views first.
            slim_with_views.sort(key=lambda x: x.get("_views", 0), reverse=True)
            slim_items: list[dict] = []
            for rank, row in enumerate(slim_with_views, start=1):
                slim_items.append({
                    "id": row["id"],
                    "title": row["title"],
                    "caption": row["caption"],
                    "hashtags": row["hashtags"],
                    "rank": rank,
                })

            # ── Write raw file (full, with UUIDs — agent-blocked) ───
            await _write_json_to_gcs(chat_id, f"searches_raw/search_{search_number}.json", {
                "search_number": search_number,
                "search_id": str(search_id),
                "query": nq,
                "fetched_at": fetched_at,
                "items": raw_items,
            })

            # ── Write slim ranked file (no UUIDs, no metrics) ───────
            slim_path = f"searches/search_{search_number}.json"
            await _write_json_to_gcs(chat_id, slim_path, {
                "search_number": search_number,
                "query": nq,
                "item_count": len(slim_items),
                "ranking": "views_desc",
                "items": slim_items,
            })
            files_written.append(f"/searches/search_{search_number}.json")

            # ── Progress tracking ──────────────────────────────────
            register_search(progress, search_number, nq, count, search_id=str(search_id))

            executed.append({
                "search_number": search_number,
                "query": nq,
                "item_count": count,
            })
        except Exception as e:
            msg = str(e)
            failed.append({"search_number": query_numbers[nq], "query": nq, "error": msg})
            await _record_error(progress, nq, msg)

    await asyncio.gather(*[_worker(nq) for nq in unique_queries])

    # Persist progress
    await _write_prog(chat_id, progress)

    tool_output = {
        "executed": sorted(executed, key=lambda x: x["search_number"]),
        "failed": failed,
        "files_written": files_written,
    }

    await _append_jsonl_to_gcs(
        chat_id,
        "tool_calls.jsonl",
        {
            "ts": _now_iso(),
            "tool": "deep_search_batch_wait",
            "input": {"queries": queries or []},
            "output": tool_output,
            "writes": ["progress.json"] + files_written,
        },
    )

    return tool_output
