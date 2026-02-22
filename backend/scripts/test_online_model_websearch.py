#!/usr/bin/env python3
"""Quick smoke test for OpenRouter online model web search behavior.

Usage:
  cd backend
  python3 scripts/test_online_model_websearch.py

Optional:
  python3 scripts/test_online_model_websearch.py --question "..."
  python3 scripts/test_online_model_websearch.py --model "openrouter/x-ai/grok-4.1-fast:online"
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure `app` package is importable when script is run from repo root or backend/.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.model_factory import init_chat_model


DEFAULT_MODEL = "openrouter/x-ai/grok-4.1-fast:online"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test :online model web search behavior.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name to test.")
    parser.add_argument(
        "--question",
        default=(
            "As of now, give me 2 current AI headlines from the web. "
            "For each, include: title, publication, published date (YYYY-MM-DD), and source URL. "
            "If browsing is unavailable, respond exactly with CANNOT_BROWSE."
        ),
        help="Prompt to send to the model.",
    )
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature.")
    return parser.parse_args()


def _extract_text(content: object) -> str:
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


def _evaluate_response(text: str) -> tuple[bool, dict]:
    urls = re.findall(r"https?://[^\s)>\]}]+", text)
    dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    blocked = "CANNOT_BROWSE" in text
    # Simple smoke-test heuristic: model should return at least 2 URLs and 2 ISO dates.
    ok = (not blocked) and len(urls) >= 2 and len(dates) >= 2
    return ok, {
        "blocked_marker_found": blocked,
        "url_count": len(urls),
        "date_count": len(dates),
    }


async def _run() -> int:
    args = _parse_args()
    now_utc = datetime.now(timezone.utc).isoformat()

    llm = init_chat_model(args.model, temperature=args.temperature)
    response = await llm.ainvoke(
        f"Current UTC timestamp: {now_utc}\n\n{args.question}"
    )
    text = _extract_text(getattr(response, "content", response))
    ok, checks = _evaluate_response(text)

    print(f"Model: {args.model}")
    print(f"Timestamp: {now_utc}")
    print(f"Heuristic: {'PASS' if ok else 'FAIL'}")
    print(f"Checks: {checks}")
    print("\n--- Model Response ---")
    print(text)
    print("--- End Response ---")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
