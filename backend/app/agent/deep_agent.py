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
    get_search_items,
)
from app.agent.deep_research_tools import (
    deep_search_wait,
    deep_analyze_batch_with_criteria,
    write_scores_and_stats,
    create_final_report,
)


# Context schema for deep agent - enables runtime.context access
class DeepAgentContext(TypedDict):
    chat_id: str


ORCHESTRATOR_PROMPT = """You are the Deep Research Orchestrator for ContHunt.
You must coordinate subagents and file handoffs to answer the user's request.
You are talking to a human user and do NOT have access to files. Never tell the user to open files or reference them.
Files are only for internal agent coordination. Your final response must be complete and self-contained without citing files.

Workflow:
1. Write a brief plan to `/plan.md`.
2. If searches are needed, delegate to the `searcher` subagent.
3. After searches complete, delegate to the `analyzer` subagent with the goal and search IDs.
4. Call `create_final_report()` to get the top 30 results (IDs + scores + justifications).
5. Call `report_chosen_videos([...])` with those top 30 IDs.
6. Respond to the user with a complete, self-contained answer (no file references).

File rules:
- Store all artifacts under `/`.
- Prefer JSON for machine data and Markdown for narrative.
"""


SEARCHER_PROMPT = """You are the Search subagent.
Goal: Run only the necessary searches to answer the user's request.

Rules:
- Do NOT run all possible searches. You can run atmost 5 parallely (spawn 5 deep_search_wait tool calls) at a time
- Use `deep_search_wait(query)` to run a single search and wait for completion.
- Return a short summary of what you searched and what was found.
- If any search fails, ignore it and continue.
- Do NOT read searches.json.
"""


ANALYZER_PROMPT = """You are the Analysis subagent.
Goal: Score videos based on justifications and criteria.

Rules:
- Analyze in batches of 25, sorted by views (highest first).
- Call `deep_analyze_batch_with_criteria(criteria)` to run the next batch and write justifications.
- Score each video using the criteria from the tool results only (similarity score 0-1).
- Call `write_scores_and_stats(scores)` to persist scores and get stats.
- Continue batches until you have >=50 videos with score >=0.9 or you run out of videos.
- Do NOT write any files directly. Return only a brief summary of video types analyzed.
"""


def build_deep_agent(checkpointer=None, model_name: str | None = None):
    settings = get_settings()
    model = init_chat_model(model_name or "openrouter/google/gemini-3-flash-preview", temperature=0.5)

    def backend(rt):
        
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
            "description": "Run targeted searches and record search IDs.",
            "system_prompt": SEARCHER_PROMPT,
            "tools": [deep_search_wait],
        },
        {
            "name": "analyzer",
            "description": "Filter videos, run analysis, and record chosen IDs.",
            "system_prompt": ANALYZER_PROMPT,
            "tools": [deep_analyze_batch_with_criteria, write_scores_and_stats],
        },
    ]

    return create_deep_agent(
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[report_chosen_videos, create_final_report],
        subagents=subagents,
        backend=backend,
        checkpointer=checkpointer,
        context_schema=DeepAgentContext,  # Enable runtime.context
    )
