from __future__ import annotations

from typing import Any, List

from app.agent.deep_research import gcs_store


async def load_search_items(chat_id: str, search_id: str) -> List[dict]:
    detail = await gcs_store.read_json(chat_id, f"search_{search_id}_detail.json")
    if not isinstance(detail, dict):
        return []
    items = detail.get("summary_items") or []
    return items if isinstance(items, list) else []


def view_count(item: dict) -> int:
    metrics = item.get("metrics") or {}
    try:
        return int(metrics.get("view_count") or 0)
    except Exception:
        return 0


def sort_by_views_desc(items: List[dict]) -> List[dict]:
    return sorted(items, key=view_count, reverse=True)


def extract_title(item: dict) -> str:
    t = item.get("title")
    return str(t).strip() if t else ""

