from __future__ import annotations

from typing import Any

from app.agent.telemetry.redaction import redact
from app.integrations.langfuse_client import AgentRunContext, get_langfuse_callback_handler


def attach_langfuse_to_config(
    config: dict[str, Any] | None,
    run_context: AgentRunContext,
    *,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    next_config: dict[str, Any] = dict(config or {})

    next_tags = list(next_config.get("tags") or [])
    next_tags.extend(tags or [])
    next_tags.extend([run_context.feature, run_context.operation])
    # Preserve order while deduplicating.
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in next_tags:
        if not tag or tag in seen:
            continue
        seen.add(tag)
        unique_tags.append(tag)
    next_config["tags"] = unique_tags
    if not next_config.get("run_name"):
        next_config["run_name"] = f"{run_context.feature}.{run_context.operation}"

    metadata = dict(next_config.get("metadata") or {})
    metadata.update(redact(run_context.metadata()))
    if run_context.user_id:
        metadata["langfuse_user_id"] = run_context.user_id
    if run_context.session_id:
        metadata["langfuse_session_id"] = run_context.session_id
    metadata["langfuse_tags"] = unique_tags
    next_config["metadata"] = metadata

    handler = get_langfuse_callback_handler()
    if handler is not None:
        callbacks = list(next_config.get("callbacks") or [])
        callbacks.append(handler)
        next_config["callbacks"] = callbacks

    return next_config
