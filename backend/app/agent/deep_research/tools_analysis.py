"""Analyzer tools: research_videos and read_research_results.

- research_videos: batch QA over videos from multiple searches.
  Analyzes on-the-fly if needed, answers a question per video with strict scoring.
- read_research_results: read back results from a slug file with pagination + filtering.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.deep_research import cache, gcs_store
from app.agent.deep_research.justification import answer_and_score
from app.agent.deep_research.progress import read_progress
from app.core import get_settings
from app.core.logging import logger

settings = get_settings()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(val: Any) -> int:
    try:
        return int(val or 0)
    except Exception:
        return 0


def _get_chat_id(config: RunnableConfig) -> str | None:
    return (config.get("configurable") or {}).get("chat_id")


async def _load_videos_for_searches(
    chat_id: str,
    search_names: list[str],
    top_per_search: int,
) -> tuple[list[dict], list[str]]:
    """Load top-ranked videos from multiple searches, interleaved by rank.

    Returns (merged_items, errors).
    Each item has: ref, search_query, video_id, media_asset_id, title,
    platform, creator, views, likes, caption, hashtags.
    """
    progress = await read_progress(chat_id)

    # Build query → search_number mapping
    query_to_num: dict[str, int] = {}
    for s in progress.get("searches_v2", []):
        query_to_num[s.get("query", "")] = int(s["number"])

    # Load items per search
    per_search: dict[str, list[dict]] = {}
    errors: list[str] = []

    for name in search_names:
        search_number = query_to_num.get(name)
        if search_number is None:
            logger.warning("[DEEP_RESEARCH] search '%s' not found in progress", name)
            errors.append(f"Search not found: '{name}'")
            continue

        # Try ranked file first, fallback to regular
        ranked = await gcs_store.read_json(
            chat_id, f"searches/search_{search_number}_ranked.json"
        )
        if isinstance(ranked, dict) and ranked.get("ranked_items"):
            items = ranked["ranked_items"]
            logger.info("[DEEP_RESEARCH] search '%s' (N=%d): loaded %d items from _ranked.json", name, search_number, len(items))
        elif isinstance(ranked, dict) and ranked.get("items"):
            items = ranked["items"]
            logger.info("[DEEP_RESEARCH] search '%s' (N=%d): loaded %d items from _ranked.json (items key)", name, search_number, len(items))
        else:
            slim = await gcs_store.read_json(
                chat_id, f"searches/search_{search_number}.json"
            )
            items = (slim or {}).get("items", []) if isinstance(slim, dict) else []
            logger.info("[DEEP_RESEARCH] search '%s' (N=%d): fallback to search.json, loaded %d items", name, search_number, len(items))

        # Load raw file for media_asset_id resolution
        raw = await gcs_store.read_json(
            chat_id, f"searches_raw/search_{search_number}.json"
        )
        raw_items_by_id: dict[int, dict] = {}
        if isinstance(raw, dict):
            for ri in raw.get("items", []):
                raw_items_by_id[ri.get("video_id", -1)] = ri

        # Enrich each item with media_asset_id from raw
        enriched: list[dict] = []
        skipped_no_media = 0
        for it in items[:top_per_search]:
            vid = it.get("id") or it.get("video_id")
            if vid is None:
                continue
            vid = int(vid)
            raw_item = raw_items_by_id.get(vid, {})
            media_asset_id = raw_item.get("media_asset_id")
            if not media_asset_id:
                skipped_no_media += 1
                continue

            metrics = raw_item.get("metrics") or {}
            enriched.append({
                "ref": f"{name}:V{vid}",
                "search_query": name,
                "video_id": vid,
                "media_asset_id": media_asset_id,
                "title": it.get("title") or raw_item.get("title") or "",
                "platform": it.get("platform") or raw_item.get("platform") or "",
                "creator": it.get("creator") or raw_item.get("creator_handle") or "",
                "views": _safe_int(it.get("views") or metrics.get("view_count")),
                "likes": _safe_int(it.get("likes") or metrics.get("like_count")),
                "caption": it.get("caption") or raw_item.get("caption") or "",
                "hashtags": it.get("hashtags") or raw_item.get("hashtags") or [],
            })

        if skipped_no_media:
            logger.warning("[DEEP_RESEARCH] search '%s': skipped %d items (no media_asset_id in raw)", name, skipped_no_media)
        logger.info("[DEEP_RESEARCH] search '%s': enriched %d videos for analysis", name, len(enriched))
        per_search[name] = enriched

    # Interleave round-robin by rank across searches
    merged: list[dict] = []
    max_len = max((len(v) for v in per_search.values()), default=0)
    search_keys = [n for n in search_names if n in per_search]
    for rank in range(max_len):
        for name in search_keys:
            items_list = per_search[name]
            if rank < len(items_list):
                merged.append(items_list[rank])

    return merged, errors


@tool
async def research_videos(
    searches: list[str],
    question: str,
    slug: str,
    config: RunnableConfig,
    top_per_search: int = 30,
) -> dict:
    """Research videos by answering a question for each video with a strict relevance score.

    For each video:
    1. Runs full video analysis if not already cached (on-the-fly)
    2. Answers the research question based on the full analysis
    3. Assigns a strict 1-10 relevance score

    Results are written to {slug}.json for later retrieval via read_research_results.

    Args:
        searches: Search NAMES (query text, not numbers).
                  Example: ["viral cooking hacks", "kitchen fails"]
        question: The research question to answer per video.
                  Example: "How relevant is this to fitness brand strategy?"
        slug: Output file name (without .json). Example: "initial-research"
        top_per_search: Max videos to include from each search (default 30).
    """
    chat_id = _get_chat_id(config)
    if not chat_id:
        return {"error": "chat_id is required"}

    if not searches:
        return {"error": "searches list is required"}
    if not question or not question.strip():
        return {"error": "question is required"}
    if not slug or not slug.strip():
        return {"error": "slug is required"}

    slug = slug.strip()

    # Load and merge videos from all searches
    logger.info("[DEEP_RESEARCH] research_videos START slug=%s searches=%s top_per_search=%d", slug, searches, top_per_search)
    merged, load_errors = await _load_videos_for_searches(
        chat_id, searches, top_per_search
    )
    logger.info("[DEEP_RESEARCH] research_videos loaded %d total videos across %d searches", len(merged), len(searches))

    if not merged:
        return {
            "error": "No videos found across the specified searches",
            "search_errors": load_errors,
        }

    concurrency = int(getattr(settings, "DEEP_RESEARCH_ANALYSIS_CONCURRENCY", 50))
    sem = asyncio.Semaphore(concurrency)
    results: list[dict] = [None] * len(merged)  # type: ignore[list-item]
    failed_count = 0

    async def _process_one(idx: int, video: dict) -> None:
        nonlocal failed_count
        async with sem:
            try:
                logger.info("[DEEP_RESEARCH] processing %d/%d ref=%s media_asset=%s", idx + 1, len(merged), video["ref"], video["media_asset_id"])
                # Ensure analysis exists (runs on-the-fly if absent)
                analysis_str = await cache.ensure_analysis(
                    chat_id, video["media_asset_id"], config
                )
                logger.info("[DEEP_RESEARCH] analysis ready for ref=%s (len=%d)", video["ref"], len(analysis_str))

                # Build compact metadata string for the LLM
                meta = (
                    f"Platform: {video['platform']} | Creator: {video['creator']} | "
                    f"Views: {video['views']:,} | Likes: {video['likes']:,}\n"
                    f"Caption: {video['caption'][:200]}\n"
                    f"Hashtags: {', '.join(video['hashtags'][:10])}"
                )

                # LLM: answer question + score
                result = await answer_and_score(
                    question=question,
                    title=video["title"],
                    analysis_str=analysis_str,
                    video_meta=meta,
                    config=config,
                )

                results[idx] = {
                    "ref": video["ref"],
                    "search_query": video["search_query"],
                    "video_id": video["video_id"],
                    "media_asset_id": video["media_asset_id"],
                    "title": video["title"],
                    "platform": video["platform"],
                    "creator": video["creator"],
                    "views": video["views"],
                    "likes": video["likes"],
                    "score": result.score,
                    "answer": result.answer,
                }
            except Exception as e:
                logger.warning(
                    "research_videos: failed on %s: %s", video["ref"], str(e)
                )
                failed_count += 1
                results[idx] = {
                    "ref": video["ref"],
                    "search_query": video["search_query"],
                    "video_id": video["video_id"],
                    "media_asset_id": video["media_asset_id"],
                    "title": video["title"],
                    "platform": video["platform"],
                    "creator": video["creator"],
                    "views": video["views"],
                    "likes": video["likes"],
                    "score": 0,
                    "answer": f"[FAILED] {str(e)[:200]}",
                }

    await asyncio.gather(*[_process_one(i, v) for i, v in enumerate(merged)])

    # Filter out None entries (shouldn't happen but be safe)
    final_items = [r for r in results if r is not None]

    # Compute score distribution
    score_dist = {"1-3": 0, "4-5": 0, "6-7": 0, "8-9": 0, "10": 0, "failed": 0}
    for item in final_items:
        s = item["score"]
        if s == 0:
            score_dist["failed"] += 1
        elif s <= 3:
            score_dist["1-3"] += 1
        elif s <= 5:
            score_dist["4-5"] += 1
        elif s <= 7:
            score_dist["6-7"] += 1
        elif s <= 9:
            score_dist["8-9"] += 1
        else:
            score_dist["10"] += 1

    # Write to GCS
    logger.info("[DEEP_RESEARCH] research_videos COMPLETE slug=%s total=%d failed=%d scores=%s", slug, len(final_items), failed_count, score_dist)
    payload = {
        "slug": slug,
        "question": question,
        "created_at": _now_iso(),
        "searches_used": searches,
        "total_items": len(final_items),
        "total_failed": failed_count,
        "score_distribution": score_dist,
        "items": final_items,
    }
    logger.info("[DEEP_RESEARCH] writing slug=%s.json to GCS (%d items)", slug, len(final_items))
    await gcs_store.write_json(chat_id, f"{slug}.json", payload)

    return {
        "slug": slug,
        "file": f"/{slug}.json",
        "total_processed": len(final_items),
        "total_failed": failed_count,
        "score_distribution": score_dist,
        "search_errors": load_errors,
    }


@tool
async def read_research_results(
    slug: str,
    config: RunnableConfig,
    index_range: list[int] | None = None,
    min_score: int = 0,
    sort_by: str = "order",
) -> dict:
    """Read back research results from a slug file with pagination and filtering.

    Args:
        slug: The slug name of the research file (without .json).
        index_range: [start, end] 0-indexed inclusive range. Default: all items.
        min_score: Minimum score to include (default 0 = all).
        sort_by: "order" (original interleaved order) or "score" (descending).
    """
    chat_id = _get_chat_id(config)
    if not chat_id:
        return {"error": "chat_id is required"}

    data = await gcs_store.read_json(chat_id, f"{slug.strip()}.json")
    if not isinstance(data, dict):
        return {"error": f"Research file not found: {slug}.json"}

    items = data.get("items", [])
    if not isinstance(items, list):
        return {"error": f"Invalid research file format: {slug}.json"}

    # Filter by score
    if min_score > 0:
        items = [it for it in items if it.get("score", 0) >= min_score]

    # Sort
    if sort_by == "score":
        items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)

    # Slice by range
    total_after_filter = len(items)
    if index_range and len(index_range) == 2:
        start, end = int(index_range[0]), int(index_range[1])
        items = items[start : end + 1]  # inclusive end
    actual_range = [0, len(items) - 1] if items else [0, 0]

    # Strip media_asset_id from agent-facing output
    agent_items = []
    for it in items:
        agent_items.append({
            "ref": it.get("ref", ""),
            "title": it.get("title", ""),
            "platform": it.get("platform", ""),
            "creator": it.get("creator", ""),
            "views": it.get("views", 0),
            "likes": it.get("likes", 0),
            "score": it.get("score", 0),
            "answer": it.get("answer", ""),
        })

    return {
        "slug": slug,
        "question": data.get("question", ""),
        "total_in_file": data.get("total_items", 0),
        "total_after_filter": total_after_filter,
        "returned_count": len(agent_items),
        "range": actual_range,
        "items": agent_items,
    }
