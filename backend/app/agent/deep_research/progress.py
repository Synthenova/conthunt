from __future__ import annotations

from datetime import datetime, timezone

from app.agent.deep_research import gcs_store


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _defaults() -> dict:
    return {
        "next_search_number": 1,
        "searches_v2": [],
        "last_updated_at": _now_iso(),
    }


async def read_progress(chat_id: str) -> dict:
    data = await gcs_store.read_json(chat_id, "progress.json")
    if not isinstance(data, dict):
        data = _defaults()
    data.setdefault("next_search_number", 1)
    data.setdefault("searches_v2", [])
    return data


async def write_progress(chat_id: str, progress: dict) -> None:
    progress["last_updated_at"] = _now_iso()
    await gcs_store.write_json(chat_id, "progress.json", progress)


# ---------------------------------------------------------------------------
# Numbered search helpers
# ---------------------------------------------------------------------------

def get_next_search_number(progress: dict) -> int:
    """Return the next available search number."""
    return int(progress.get("next_search_number") or 1)


def register_search(
    progress: dict,
    search_number: int,
    query: str,
    item_count: int,
    search_id: str = "",
) -> None:
    """Register a completed search in progress."""
    searches_v2 = progress.get("searches_v2")
    if not isinstance(searches_v2, list):
        searches_v2 = []
    searches_v2.append({
        "number": search_number,
        "query": query,
        "item_count": item_count,
    })
    progress["searches_v2"] = searches_v2
