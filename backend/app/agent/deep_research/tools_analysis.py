from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.deep_research import cache, criteria_outputs, progress, search_inventory
from app.agent.deep_research.justification import justify_with_score
from app.agent.model_factory import init_chat_model
from app.core import get_settings
from app.llm.context import set_llm_context

settings = get_settings()


def _get_chat_id(config: RunnableConfig) -> str | None:
    return ((config or {}).get("configurable") or {}).get("chat_id")


@tool
async def analyze_search_batch_with_criteria(
    search_ids: list[str],
    count_per_search: int,
    criteria: str,
    criteria_slug: str,
    config: RunnableConfig,
) -> dict:
    """
    Analyze the top-by-views, not-yet-processed videos from each search_id for a given criteria_slug.
    Writes a new <criteria_slug>-NNN.json file every run. Returns stats only.
    """
    chat_id = _get_chat_id(config)
    if not chat_id:
        return {"error": "chat_id is required"}

    requested = max(0, int(count_per_search or 0))
    if requested <= 0:
        return {"error": "count_per_search must be > 0"}
    if not criteria_slug or not str(criteria_slug).strip():
        return {"error": "criteria_slug is required"}

    if not isinstance(search_ids, list) or not search_ids:
        return {"error": "search_ids must be a non-empty list"}

    # Concurrency for analysis + justification across ALL selected videos.
    import asyncio
    sem = asyncio.Semaphore(settings.DEEP_RESEARCH_ANALYSIS_CONCURRENCY)

    async def _one(it: dict) -> dict:
        mid = str(it.get("media_asset_id"))
        title = search_inventory.extract_title(it)
        async with sem:
            analysis_str = await cache.ensure_analysis(chat_id, mid, config)
            j = await justify_with_score(criteria=criteria, title=title, analysis_str=analysis_str, config=config)
        return {
            "media_asset_id": mid,
            "title": title,
            "reason": j.reason,
            "score": float(j.score),
        }

    output_payload: Dict[str, List[dict]] = {}
    stats: Dict[str, dict] = {}
    total_analyzed = 0

    for raw_sid in search_ids:
        sid = str(raw_sid).strip()
        if not sid:
            continue

        items = await search_inventory.load_search_items(chat_id, sid)
        if not items:
            output_payload[sid] = []
            stats[sid] = {
                "requested": requested,
                "analyzed": 0,
                "skipped_already_done": 0,
                "status": "missing_or_empty_search_detail",
            }
            continue

        items = search_inventory.sort_by_views_desc(items)
        done = await criteria_outputs.read_done_media_ids(chat_id, str(criteria_slug), sid)
        selected: List[dict] = []
        skipped_already_done = 0
        for it in items:
            mid = it.get("media_asset_id")
            if not mid:
                continue
            mid = str(mid)
            if mid in done:
                skipped_already_done += 1
                continue
            selected.append(it)
            if len(selected) >= requested:
                break

        if not selected:
            output_payload[sid] = []
            stats[sid] = {
                "requested": requested,
                "analyzed": 0,
                "skipped_already_done": skipped_already_done,
                "status": "nothing_new_to_analyze",
            }
            continue

        rows = await asyncio.gather(*[_one(it) for it in selected], return_exceptions=True)
        out_rows: List[dict] = []
        for r in rows:
            if isinstance(r, Exception):
                continue
            out_rows.append(r)

        output_payload[sid] = out_rows
        stats[sid] = {
            "requested": requested,
            "analyzed": len(out_rows),
            "skipped_already_done": skipped_already_done,
            "status": "ok",
        }
        total_analyzed += len(out_rows)

    prog = await progress.read_progress(chat_id)
    for sid, st in stats.items():
        progress.bump_criteria_counts(prog, str(criteria_slug), str(sid), analyzed_inc=int(st.get("analyzed") or 0))
    await progress.write_progress(chat_id, prog)

    existing = await criteria_outputs.list_criteria_files(chat_id, str(criteria_slug))
    written_file = criteria_outputs.next_filename(str(criteria_slug), existing)
    await criteria_outputs.write_criteria_batch(chat_id, written_file, output_payload)

    return {
        "criteria_slug": str(criteria_slug),
        "search_ids": [str(s).strip() for s in (search_ids or []) if str(s).strip()],
        "count_per_search": requested,
        "total_analyzed": total_analyzed,
        "stats": stats,
        "written_file": written_file,
    }


@tool
async def answer_video_question(
    media_asset_id: str,
    question: str,
    config: RunnableConfig,
) -> str:
    """
    Answer an arbitrary question about a video using cached analysis if available.
    Returns a plain string only.
    """
    chat_id = _get_chat_id(config)
    if not chat_id:
        return "Error: chat_id is required."

    mid = str(media_asset_id)
    q = (question or "").strip()
    if not q:
        return "Error: question is required."

    analysis_str = await cache.ensure_analysis(chat_id, mid, config)

    model = init_chat_model(settings.DEEP_RESEARCH_MODEL, temperature=0.2)
    system = SystemMessage(
        content=(
            "Answer the user's question using the provided video analysis.\n"
            "Be concise and specific. Do not dump the full analysis."
        )
    )
    human = HumanMessage(content=f"Question:\n{q}\n\nVideo analysis:\n{analysis_str}")

    user_id = (config.get("configurable") or {}).get("user_id")
    with set_llm_context(user_id=user_id, route="deep_research.qa"):
        resp = await model.ainvoke([system, human])
    return str(getattr(resp, "content", resp)).strip()
