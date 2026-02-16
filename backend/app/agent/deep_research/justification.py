from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.model_factory import init_chat_model
from app.llm.context import set_llm_context
from app.core import get_settings

settings = get_settings()


class AnswerAndScoreOut(BaseModel):
    score: int = Field(..., description="Relevance score 1-10")
    answer: str = Field(..., description="Detailed answer to the research question about this video")


_SCORING_SYSTEM = """\
You are evaluating a video against a research question.

Provide:
1. A relevance SCORE from 1-10
2. A concise ANSWER (80-120 words) explaining how this video relates to the question

Scoring guidelines (BE STRICT):
- 1-3: Tangentially related, weak signal, little to learn from
- 4-5: Somewhat relevant but generic or unremarkable
- 6-7: Clearly relevant with some useful insights
- 8-9: Highly relevant, strong match, distinctive approach worth studying
- 10:  Exceptional — directly answers the question with unique, actionable insight

IMPORTANT: Be strict. Most videos should score 3-6.
Reserve 7+ for genuinely standout content. A score of 8+ means
"this specific video teaches something valuable about the question."

Your answer should briefly cover:
- How the video relates to the research question
- What specific strategies, techniques, or approaches it demonstrates
- What makes it stand out (or not)
- What could be learned from it
"""


async def answer_and_score(
    *,
    question: str,
    title: str,
    analysis_str: str,
    video_meta: str,
    config: RunnableConfig,
) -> AnswerAndScoreOut:
    """Answer a research question about a video and score its relevance.

    Args:
        question: The research question to answer.
        title: The video title.
        analysis_str: Full video analysis text (~3k tokens).
        video_meta: Compact metadata string (platform, creator, views, etc).
        config: Runnable configuration.

    Returns:
        AnswerAndScoreOut with score (1-10) and answer (80-120 words).
    """
    model = init_chat_model(settings.DEEP_RESEARCH_MODEL, temperature=0.2)

    try:
        structured = model.with_structured_output(AnswerAndScoreOut)
    except Exception:
        structured = None

    system = SystemMessage(content=_SCORING_SYSTEM)
    human = HumanMessage(
        content=(
            f"Research Question:\n{question}\n\n"
            f"Video: {title}\n{video_meta}\n\n"
            f"Full Video Analysis:\n{analysis_str}\n"
        )
    )

    user_id = (config.get("configurable") or {}).get("user_id")
    with set_llm_context(user_id=user_id, route="deep_research.answer_and_score"):
        if structured is not None:
            out = await structured.ainvoke([system, human])
            if isinstance(out, AnswerAndScoreOut):
                return out
            return AnswerAndScoreOut.model_validate(out)

        # Fallback: ask for JSON
        fallback_model = model
        resp = await fallback_model.ainvoke(
            [
                SystemMessage(content=system.content + "\nReturn JSON with keys: score, answer."),
                human,
            ]
        )
        text = str(getattr(resp, "content", resp))
        import json
        return AnswerAndScoreOut.model_validate(json.loads(text))
