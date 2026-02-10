"""Deep Agents setup for ContHunt Deep Research mode."""
from __future__ import annotations

from typing_extensions import TypedDict

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend

from app.core import get_settings
from app.agent.deepagent_gcs_backend import GCSBackend
from app.agent.model_factory import init_chat_model
from app.agent.tools import (
    report_chosen_videos,
)
from app.agent.deep_research_tools import (
    deep_search_batch_wait,
    get_search_overview,
    analyze_search_batch_with_criteria,
    answer_video_question,
)


# Context schema for deep agent - enables runtime.context access
# class DeepAgentContext(TypedDict):
#     chat_id: str
#     thread_id: str
#     x_auth_token: str


def build_deep_agent(checkpointer=None, model_name: str | None = None):
    settings = get_settings()
    model = init_chat_model(model_name or settings.DEEP_RESEARCH_MODEL, temperature=0.5)
    # Searcher subagent uses a stronger model with Google Search grounding enabled.
    searcher_model = init_chat_model("google/gemini-3-pro-preview", temperature=0.2)
    searcher_model_with_search = searcher_model.bind_tools([{"google_search": {}}])

    orchestrator_prompt = f"""You are the Deep Research Orchestrator for ContHunt.
You must coordinate subagents and file handoffs to answer the user's request.
You are talking to a human user and do NOT have access to files. Never tell the user to open files or reference them.
Files are only for internal agent coordination. Your final response must be complete and self-contained without citing files.

Deep Research Output Contract (MUST FOLLOW):
- For any user request that is NOT casual small talk, you MUST call `report_chosen_videos(...)` before writing your final response.
- Analysis quota (per criteria_slug):
  - Before calling `report_chosen_videos(...)` for a given `criteria_slug`, you MUST ensure at least 50 UNIQUE videos have been analyzed/scored for that criteria_slug, unless fewer than 50 exist in the available pool. If fewer exist, analyze all available and proceed.
  - This 50-video analysis quota is TOTAL across all searches (not 50 per search).
  - On future turns for the SAME criteria_slug, do NOT re-analyze if you already have >= 50 analyzed; only analyze additional videos if needed to produce the next selection batch without repeats.
- Per-turn selection quota:
  - Minimum: 10 videos
  - Default: 10 videos
  - Maximum: 20 videos (hard cap even if the user asks for more; return 20).
- If the user asks for exactly 20, you MUST return 20 if at all possible (run the pipeline as needed to reach 20).
- The same per-turn quota logic (min 10, default 10, max 20) applies whenever the user asks for videos/examples again.
- Never repeat videos:
  - For the same `criteria_slug`, do NOT include any `media_asset_id` that has already been reported in any prior `report_chosen_videos` call for that slug.
  - For a new `criteria_slug`, prefer NOT to reuse previously chosen videos unless the user explicitly allows overlap.
- Efficiency rule:
  - Prefer selecting from already-analyzed/scored candidates first.
  - Prefer analyzing/scoring only the deficit needed to satisfy the analysis quota (50) and to reach the turn's selection target; do NOT analyze everything unnecessarily.

Workflow:
1. Write a brief plan to `/plan.md`.
2. If searches are needed, delegate to the `searcher` subagent.
3. Use `deep_search_batch_wait([...])` to run the proposed queries and persist progress + details.
4. If you need to inspect what a given search found, call `get_search_overview(search_id)`.
5. When you want to analyze results from one or more searches, call `analyze_search_batch_with_criteria(search_ids, count_per_search, criteria, criteria_slug)`.
6. You MUST NOT read any files under `/analysis/` directly. Use tools instead.
7. If you need a specific answer about a specific video, call `answer_video_question(media_asset_id, question)` ONLY when necessary.
8. After each `analyze_search_batch_with_criteria(...)` call, decide whether to run another analysis batch or finish selection.
9. When you have selected the target number of videos for THIS turn, call `report_chosen_videos(chosen, criteria_slug)` where chosen is a list of {{"media_asset_id": "...", "reason": "..."}}.
10. On the next user turn, decide whether to continue the same criteria_slug (more batches) or use a new criteria_slug.
11. Respond to the user with a complete, self-contained answer (no file references). Start with 1-2 lines summarizing what you did this turn, then briefly explain the chosen videos and why they fit.
12. STRICT OVERRIDE: If the user provides a specific number for total videos to analyze, or a specific number of final videos to select, you MUST strictly follow those numbers and override any default counts mentioned in these instructions.

File rules:
- Store all artifacts under `/`.
- Prefer JSON for machine data and Markdown for narrative.
"""

    searcher_prompt = f"""You are the Search subagent.
Goal: Propose only the necessary search queries to answer the user's request.

Rules:
- Do NOT run tools. The orchestrator will execute searches.
- Return ONLY valid JSON with this shape: {{"queries": ["...","..."]}}.
- STRICT LIMIT: Never propose more than 4 queries.
- STRICT OVERRIDE: If the user requests a specific number of search queries, you MUST provide exactly that many queries, ignoring the default suggestion.
- These queries will be used as *in-app* search keywords on TikTok, YouTube, and Instagram. Write them the way people actually search on those platforms (short, high-signal, phrase-like).
- Do NOT include platform names (no "tiktok", "youtube", "instagram") in the keywords.
"""

    def backend(rt):
        print("rt", rt)
        # Primary: config.configurable (always passed reliably from API)
        cfg = getattr(rt, "config", None) or {}
        configurable = cfg.get("configurable") or {}
        chat_id = configurable.get("chat_id")

        # Secondary: runtime.context (if context_schema + context= is used)
        if not chat_id:
            ctx = getattr(rt, "context", None) or {}
            chat_id = ctx.get("chat_id") if hasattr(ctx, "get") else None

        # Last resort: thread_id fallback so we never hard-fail
        if not chat_id:
            chat_id = configurable.get("thread_id")

        if not chat_id:
            raise ValueError("chat_id (or thread_id fallback) required for deep agent filesystem root prefix")

        return CompositeBackend(
            default=GCSBackend(
                bucket_name=settings.GCS_DEEPAGNT_FS,
                root_prefix=f"deepagents/{chat_id}",
            ),
            routes={}
        )

    subagents = [
        {
            "name": "searcher",
            "description": "Propose targeted search queries (no tools).",
            "system_prompt": searcher_prompt,
            "model": searcher_model_with_search,
            "tools": []
        }
    ]

    return create_deep_agent(
        model=model,
        system_prompt=orchestrator_prompt,
        tools=[
            report_chosen_videos,
            deep_search_batch_wait,
            get_search_overview,
            analyze_search_batch_with_criteria,
            answer_video_question,
        ],
        subagents=subagents,
        backend=backend,
        checkpointer=checkpointer,
        # context_schema=DeepAgentContext,  # Enable runtime.context
    )
