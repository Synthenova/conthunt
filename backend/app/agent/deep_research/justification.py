from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.model_factory import init_chat_model
from app.llm.context import set_llm_context
from app.core import get_settings

settings = get_settings()


class JustificationOut(BaseModel):
    score: float = Field(..., description="Similarity score 0.0 to 1.0")
    reason: str = Field(..., description="Detailed justification for the score")


async def justify_with_score(
    *,
    criteria: str,
    title: str,
    analysis_str: str,
    config: RunnableConfig,
) -> JustificationOut:
    """
    Internal helper: produce a score + detailed justification, without exposing raw analysis.
    """
    model = init_chat_model(settings.DEEP_RESEARCH_MODEL, temperature=0.2)

    # Prefer structured output if supported by the model wrapper.
    try:
        structured = model.with_structured_output(JustificationOut)
    except Exception:
        structured = None

    system = SystemMessage(
        content=(
            "You score a video against criteria.\n"
            "Return a score from 0.0 to 1.0 and a detailed justification.\n"
            "Do not include the full raw analysis in the reason."
        )
    )
    human = HumanMessage(
        content=(
            f"Criteria:\n{criteria}\n\n"
            f"Title:\n{title}\n\n"
            f"Video analysis:\n{analysis_str}\n"
        )
    )

    user_id = (config.get("configurable") or {}).get("user_id")
    with set_llm_context(user_id=user_id, route="deep_research.justify"):
        if structured is not None:
            out = await structured.ainvoke([system, human])
            if isinstance(out, JustificationOut):
                return out
            # Some wrappers return dict
            return JustificationOut.model_validate(out)

        # Fallback: ask for JSON and parse it
        fallback_model = model
        resp = await fallback_model.ainvoke(
            [
                SystemMessage(content=system.content + "\nReturn JSON with keys: score, reason."),
                human,
            ]
        )
        text = str(getattr(resp, "content", resp))
        # Best-effort parse; if invalid, raise.
        import json

        return JustificationOut.model_validate(json.loads(text))

