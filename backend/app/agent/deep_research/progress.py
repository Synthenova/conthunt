from __future__ import annotations

from datetime import datetime, timezone

from app.agent.deep_research import gcs_store


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _defaults() -> dict:
    return {
        "search_order": [],
        "searches": {},
        "criteria": {},
        "last_updated_at": _now_iso(),
    }


async def read_progress(chat_id: str) -> dict:
    data = await gcs_store.read_json(chat_id, "progress.json")
    if not isinstance(data, dict):
        data = _defaults()
    data.setdefault("search_order", [])
    data.setdefault("searches", {})
    data.setdefault("criteria", {})
    return data


async def write_progress(chat_id: str, progress: dict) -> None:
    progress["last_updated_at"] = _now_iso()
    await gcs_store.write_json(chat_id, "progress.json", progress)


def bump_criteria_counts(progress: dict, criteria_slug: str, search_id: str, analyzed_inc: int) -> None:
    crit = (progress.get("criteria") or {}).get(criteria_slug)
    if not isinstance(crit, dict):
        crit = {"total_analyzed": 0, "by_search_id": {}}
    crit["total_analyzed"] = int(crit.get("total_analyzed") or 0) + int(analyzed_inc or 0)
    by = crit.get("by_search_id") or {}
    by[str(search_id)] = int(by.get(str(search_id)) or 0) + int(analyzed_inc or 0)
    crit["by_search_id"] = by
    progress.setdefault("criteria", {})
    progress["criteria"][criteria_slug] = crit

