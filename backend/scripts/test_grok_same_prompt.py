#!/usr/bin/env python3
"""Run Grok :online with the same prompt shape used by search planning."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

# Ensure `app` package is importable when script is run from repo root or backend/.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.model_factory import init_chat_model
from app.llm.context import set_llm_context


SYSTEM_PROMPT = """
IMPORTANT OVERRIDE: Not every user message is “inspiration.” First decide if the user intent is DIRECT LOOKUP vs INSPIRATION.

You are an expert search keyword generator specialized in discovering inspirational short-form videos across any niche or topic (e.g., marketing, fitness, cooking, fashion, tech, beauty, education, comedy, travel).
Keyword must not have platform specific keywords (e.g., tiktok, youtube, instagram, etc.)
Note: These keyword combinations will be used in a downstream LLM system (e.g., Gemini with grounding) that has direct web search access. Optimize them to perform strongly in web searches, surfacing native short-form video results effectively.

A) DIRECT LOOKUP (return 1-2 queries only)
Use DIRECT LOOKUP when the user input is mainly a named entity or specific target, with no “ideas/inspo/examples/hooks” wording.
Examples: show/movie/song/person/brand + qualifiers like season/episode/year/part/version.
- Output: EXACTLY 1-2 keyword combinations (the tightest literal phrase).
- Do NOT create 5 near-duplicates (no padding with “edits”, “scenes”, “reaction” unless the user asks for those).


B) INSPIRATION / DISCOVERY (return 3–5 queries, usually 5)
Use INSPIRATION when the user input is seeking ideas, examples, inspiration, or viral content.
- 2 hyper-niche: Extremely focused on the highest-signal, most authentic/viral elements from the request (e.g., raw relatable moments or peak format matches).
- 3 niche: Highly accurate and specific, capturing core themes with slight variations.
Step-by-step thinking for INSPIRATION / DISCOVERY (do this internally before outputting):
1. Decompose the user's request: Identify main themes (e.g., viral style, humor, tutorials, challenges, creative ideas), desired formats (POV, skit, reaction, day-in-the-life, hook, fail, transformation), and any sub-aspects (authenticity, low-budget, relatable struggles, surprises).
2. Infer common short-form video patterns for the niche: Use creator-style phrases that appear in real video titles (e.g., "POV ...", "day I tried ...", "funny ... fail", "before after ...", "trying viral ...").
3. Keep combinations short and compound (3-8 words max). Focus purely on descriptive core keywords.
4. Hashtags: Include only if they naturally boost relevance in the niche (e.g., popular trend tags); never force them.
5. Prioritize phrases that surface native, authentic videos via web search: Avoid anything that pulls articles, lists, or compilations (no "best", "top", "examples", "ideas list").
6. Diversify across the request's key angles (e.g., humor, virality, tutorials, relatability) while staying tightly on-topic.


If the user explicitly requests filters (date, sort), include them in `filters`.
Allowed values:
- publish_time/date_posted: this-week, yesterday, this-month, last-3-months, last-6-months, all-time
- sort_by: relevance, most-liked, date-posted
""".strip()

USER_MESSAGE = "User: looksmaxxing clavicular kick champ"


def _as_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                txt = block.get("text")
                if isinstance(txt, str):
                    parts.append(txt)
        return "\n".join(parts).strip()
    return str(content)


async def main() -> int:
    llm = init_chat_model("openrouter/x-ai/grok-4.1-fast:online")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=USER_MESSAGE),
    ]

    with set_llm_context(user_id="script:grok-test", route="search.plan"):
        response = await llm.ainvoke(messages)

    print("model: openrouter/x-ai/grok-4.1-fast:online")
    print("temperature: 0.5 (default)")
    print("\n--- response.content ---")
    print(_as_text(getattr(response, "content", response)))
    print("--- end ---")

    tool_calls = getattr(response, "tool_calls", None) or []
    if tool_calls:
        print("\n--- response.tool_calls ---")
        print(tool_calls)
        print("--- end ---")

    additional_kwargs = getattr(response, "additional_kwargs", None) or {}
    if additional_kwargs:
        print("\n--- response.additional_kwargs ---")
        print(additional_kwargs)
        print("--- end ---")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
