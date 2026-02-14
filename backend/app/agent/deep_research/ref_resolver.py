"""Resolve video refs like 'viral cooking hacks:V3' to media_asset_id UUIDs.

Agents never see UUIDs. This module is used internally by tools
to map agent-facing refs to database IDs.
"""
from __future__ import annotations

import re
from typing import Optional

from app.agent.deep_research import gcs_store
from app.agent.deep_research.progress import read_progress


_REF_RE = re.compile(r"^(.+):V(\d+)$")


def parse_ref(ref_str: str) -> tuple[str, int] | None:
    """Parse a ref like 'viral cooking hacks:V3' → (query, video_id).

    Strips surrounding brackets if present: '[viral cooking hacks:V3]' → same result.
    """
    cleaned = ref_str.strip().strip("[]")
    m = _REF_RE.match(cleaned)
    if not m:
        return None
    return m.group(1).strip(), int(m.group(2))


async def _query_to_search_number(chat_id: str, query: str) -> int | None:
    """Look up the search number for a given query string."""
    progress = await read_progress(chat_id)
    for s in progress.get("searches_v2", []):
        if s.get("query") == query:
            return int(s["number"])
    return None


async def resolve_ref(chat_id: str, ref_str: str) -> Optional[str]:
    """Resolve a single ref to a media_asset_id UUID.

    Args:
        chat_id: The chat/session ID.
        ref_str: A ref like 'viral cooking hacks:V3' or '[viral cooking hacks:V3]'.

    Returns:
        media_asset_id string or None if resolution fails.
    """
    parsed = parse_ref(ref_str)
    if not parsed:
        return None
    query, video_id = parsed

    search_number = await _query_to_search_number(chat_id, query)
    if search_number is None:
        return None

    raw = await gcs_store.read_json(chat_id, f"searches_raw/search_{search_number}.json")
    if not isinstance(raw, dict):
        return None
    for item in raw.get("items", []):
        if item.get("video_id") == video_id:
            return item.get("media_asset_id")
    return None


async def resolve_refs_batch(chat_id: str, refs: list[str]) -> dict[str, str | None]:
    """Resolve multiple refs to media_asset_id UUIDs.

    Returns a dict mapping each ref string to its media_asset_id (or None).
    Caches progress and raw file reads to avoid repeated GCS hits.
    """
    progress = await read_progress(chat_id)

    # Build query → search_number mapping
    query_to_num: dict[str, int] = {}
    for s in progress.get("searches_v2", []):
        query_to_num[s.get("query", "")] = int(s["number"])

    # Cache for raw search files
    raw_cache: dict[int, dict] = {}

    results: dict[str, str | None] = {}
    for ref_str in refs:
        parsed = parse_ref(ref_str)
        if not parsed:
            results[ref_str] = None
            continue

        query, video_id = parsed
        search_number = query_to_num.get(query)
        if search_number is None:
            results[ref_str] = None
            continue

        if search_number not in raw_cache:
            raw = await gcs_store.read_json(chat_id, f"searches_raw/search_{search_number}.json")
            raw_cache[search_number] = raw if isinstance(raw, dict) else {}

        raw_data = raw_cache[search_number]
        found = None
        for item in raw_data.get("items", []):
            if item.get("video_id") == video_id:
                found = item.get("media_asset_id")
                break
        results[ref_str] = found

    return results
