from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from app.agent.deep_research import gcs_store


_NUM_RE = re.compile(r"^(?P<slug>.+)-(?P<num>\d{3})\.json$")


async def list_criteria_files(chat_id: str, criteria_slug: str) -> List[str]:
    # Relative paths at root; we only care about exact "<slug>-NNN.json"
    paths = await gcs_store.list_paths(chat_id, f"{criteria_slug}-")
    out: List[str] = []
    for p in paths:
        if "/" in p:
            continue
        if p.startswith(f"{criteria_slug}-") and p.endswith(".json"):
            out.append(p)
    return sorted(out)


def next_filename(criteria_slug: str, existing_files: List[str]) -> str:
    max_n = 0
    for f in existing_files:
        m = _NUM_RE.match(f)
        if not m:
            continue
        if m.group("slug") != criteria_slug:
            continue
        try:
            n = int(m.group("num"))
        except Exception:
            continue
        if n > max_n:
            max_n = n
    return f"{criteria_slug}-{max_n + 1:03d}.json"


async def read_done_media_ids(chat_id: str, criteria_slug: str, search_id: str) -> Set[str]:
    done: Set[str] = set()
    files = await list_criteria_files(chat_id, criteria_slug)
    for f in files:
        payload = await gcs_store.read_json(chat_id, f)
        if not isinstance(payload, dict):
            continue
        rows = payload.get(str(search_id))
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            mid = r.get("media_asset_id")
            if mid:
                done.add(str(mid))
    return done


async def write_criteria_batch(chat_id: str, filename: str, payload: dict) -> None:
    await gcs_store.write_json(chat_id, filename, payload)

