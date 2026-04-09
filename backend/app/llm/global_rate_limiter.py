from __future__ import annotations

import asyncio
import math
import random
import time
from collections import defaultdict
from typing import Any

from upstash_ratelimit.asyncio import Ratelimit
from upstash_ratelimit.limiter import FixedWindow, SlidingWindow, TokenBucket

from app.core import get_settings, logger
from app.core.redis_client import get_global_redis
from app.integrations.posthog_client import capture_event
from app.llm.context import get_llm_route
from app.llm.model_policy import canonicalize_model_key, resolve_model_limits


class LlmRateLimited(ValueError):
    def __init__(
        self,
        *,
        kind: str,
        model_key: str,
        route: str | None = None,
        retry_after_s: float | None = None,
    ) -> None:
        self.kind = kind
        self.model_key = model_key
        self.route = route
        self.retry_after_s = retry_after_s

        msg = f"LLM rate limited ({kind}) model={model_key}"
        if route:
            msg += f" route={route}"
        if retry_after_s is not None:
            msg += f" retry_after={retry_after_s:.3f}s"
        super().__init__(msg)


def _is_background_route(route: str | None) -> bool:
    if not route:
        return False
    return route.startswith(("analysis.", "insights.", "tasks.", "deep_research.", "deep.research."))


def _extract_text_len_from_content(content: Any) -> int:
    if content is None:
        return 0
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, str):
                total += len(block)
                continue
            if isinstance(block, dict):
                if block.get("type") == "text":
                    total += len(str(block.get("text") or ""))
                else:
                    total += 1024
        return total
    if isinstance(content, dict):
        return _extract_text_len_from_content(content.get("text") or content.get("content"))
    return len(str(content))


def estimate_tokens(messages: Any, *, completion_tokens_hint: int | None = None) -> int:
    settings = get_settings()

    if isinstance(messages, dict) and "messages" in messages:
        messages = messages.get("messages")

    chars = 0
    if isinstance(messages, (list, tuple)):
        for m in messages:
            if isinstance(m, dict):
                chars += _extract_text_len_from_content(m.get("content"))
            else:
                chars += _extract_text_len_from_content(getattr(m, "content", m))
    else:
        if isinstance(messages, dict):
            chars += _extract_text_len_from_content(messages.get("content"))
        else:
            chars += _extract_text_len_from_content(getattr(messages, "content", messages))

    in_tokens = int(math.ceil(chars / 4.0))
    out_tokens = (
        int(completion_tokens_hint)
        if completion_tokens_hint is not None
        else int(settings.LLM_EST_COMPLETION_TOKENS_DEFAULT)
    )
    return max(1, in_tokens + max(0, out_tokens))


_LIMITER_COOLDOWN_UNTIL: float = 0.0
_LIMITER_INFRA_ERRORS: int = 0
_LIMITER_INFRA_LAST_LOG_AT: dict[str, float] = {}
_LIMITER_INFRA_SUPPRESSED: dict[str, int] = defaultdict(int)
_LIMITERS_BY_QUOTA: dict[tuple[int, int, int, int], tuple[Ratelimit, Ratelimit, Ratelimit]] = {}


def _in_cooldown() -> bool:
    return time.monotonic() < _LIMITER_COOLDOWN_UNTIL


def _record_limiter_infra_error(stage: str, exc: Exception) -> None:
    global _LIMITER_INFRA_ERRORS, _LIMITER_COOLDOWN_UNTIL
    settings = get_settings()
    _LIMITER_INFRA_ERRORS += 1
    now = time.monotonic()

    if _LIMITER_INFRA_ERRORS >= int(settings.LLM_LIMITER_INFRA_ERROR_BURST_THRESHOLD):
        _LIMITER_COOLDOWN_UNTIL = now + float(settings.LLM_LIMITER_INFRA_COOLDOWN_S)
        _LIMITER_INFRA_ERRORS = 0
        logger.warning(
            "[llm_rl] limiter infra cooldown activated for %.2fs after repeated errors (stage=%s)",
            float(settings.LLM_LIMITER_INFRA_COOLDOWN_S),
            stage,
        )

    last_at = _LIMITER_INFRA_LAST_LOG_AT.get(stage, 0.0)
    sample_every = max(1, int(settings.LLM_LIMITER_INFRA_LOG_SAMPLE_EVERY))
    min_interval = max(0.0, float(settings.LLM_LIMITER_INFRA_LOG_INTERVAL_S))
    suppressed = _LIMITER_INFRA_SUPPRESSED[stage] + 1
    should_log = (now - last_at) >= min_interval or suppressed >= sample_every

    if should_log:
        if suppressed > 1:
            logger.warning("[llm_rl] stage=%s suppressed_errors=%s", stage, suppressed - 1)
        logger.warning("[llm_rl] %s limiter error (fail-open): %s", stage, exc, exc_info=True)
        _LIMITER_INFRA_SUPPRESSED[stage] = 0
        _LIMITER_INFRA_LAST_LOG_AT[stage] = now
    else:
        _LIMITER_INFRA_SUPPRESSED[stage] = suppressed


def _record_limiter_infra_success() -> None:
    global _LIMITER_INFRA_ERRORS
    _LIMITER_INFRA_ERRORS = 0


def _build_limiters(*, rpm: int, tpm: int, rpd: int, tpm_burst: int) -> tuple[Ratelimit, Ratelimit, Ratelimit]:
    redis = get_global_redis()
    return (
        Ratelimit(
            redis=redis,
            limiter=SlidingWindow(max_requests=rpm, window=60, unit="s"),
            prefix=f"rl:llm:start:{rpm}",
        ),
        Ratelimit(
            redis=redis,
            limiter=TokenBucket(max_tokens=tpm_burst, refill_rate=tpm, interval=60, unit="s"),
            prefix=f"rl:llm:tpm:{tpm}:{tpm_burst}",
        ),
        Ratelimit(
            redis=redis,
            limiter=FixedWindow(max_requests=rpd, window=86400, unit="s"),
            prefix=f"rl:llm:rpd:{rpd}",
        ),
    )


def _get_limiters(*, rpm: int, tpm: int, rpd: int, tpm_burst: int) -> tuple[Ratelimit, Ratelimit, Ratelimit]:
    key = (int(rpm), int(tpm), int(rpd), int(tpm_burst))
    existing = _LIMITERS_BY_QUOTA.get(key)
    if existing is not None:
        return existing
    built = _build_limiters(rpm=key[0], tpm=key[1], rpd=key[2], tpm_burst=key[3])
    _LIMITERS_BY_QUOTA[key] = built
    return built


def _retry_after_from_reset(reset_at_s: float | None) -> float | None:
    if reset_at_s is None:
        return None
    return max(0.0, float(reset_at_s) - time.time())


async def enforce_model_global_limits(
    *,
    model_key: str,
    messages: Any,
    completion_tokens_hint: int | None = None,
) -> None:
    settings = get_settings()
    if _in_cooldown():
        return

    model_key = canonicalize_model_key(model_key)
    limits = resolve_model_limits(model_key, settings)
    route = get_llm_route()
    is_bg = _is_background_route(route)
    start_timeout = (
        float(settings.LLM_LIMIT_TIMEOUT_START_BACKGROUND_S)
        if is_bg
        else float(settings.LLM_LIMIT_TIMEOUT_START_INTERACTIVE_S)
    )
    token_timeout = (
        float(settings.LLM_LIMIT_TIMEOUT_TOKENS_BACKGROUND_S)
        if is_bg
        else float(settings.LLM_LIMIT_TIMEOUT_TOKENS_INTERACTIVE_S)
    )

    try:
        start_limiter, token_limiter, daily_limiter = _get_limiters(
            rpm=limits.rpm,
            tpm=limits.tpm,
            rpd=limits.rpd,
            tpm_burst=limits.tpm_burst,
        )
    except Exception as exc:
        _record_limiter_infra_error("init", exc)
        return

    est_tokens = estimate_tokens(messages, completion_tokens_hint=completion_tokens_hint)
    if est_tokens > int(limits.tpm_burst):
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={
                "model_key": model_key,
                "kind": "tpm_call_too_large",
                "route": route,
                "est_tokens": est_tokens,
                "tpm_burst": limits.tpm_burst,
            },
        )
        raise LlmRateLimited(
            kind="tpm_call_too_large",
            model_key=model_key,
            route=route,
            retry_after_s=None,
        )

    k_rpd = f"model:{model_key}:rpd"
    k_start = f"model:{model_key}:start"
    k_tpm = f"model:{model_key}:tpm"

    try:
        rpd_response = await daily_limiter.limit(k_rpd)
    except Exception as exc:
        _record_limiter_infra_error("daily", exc)
        rpd_response = None
    if rpd_response is not None and not rpd_response.allowed:
        retry_after = _retry_after_from_reset(rpd_response.reset)
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={"model_key": model_key, "kind": "rpd", "route": route, "retry_after_s": retry_after},
        )
        raise LlmRateLimited(kind="rpd", model_key=model_key, route=route, retry_after_s=retry_after)

    try:
        start_response = await start_limiter.block_until_ready(k_start, timeout=start_timeout)
    except Exception as exc:
        _record_limiter_infra_error("start", exc)
        start_response = None
    if start_response is not None and not start_response.allowed:
        retry_after = _retry_after_from_reset(start_response.reset)
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={"model_key": model_key, "kind": "rpm", "route": route, "retry_after_s": retry_after},
        )
        raise LlmRateLimited(kind="rpm", model_key=model_key, route=route, retry_after_s=retry_after)

    await asyncio.sleep(random.uniform(0, 0.05))

    try:
        token_response = await token_limiter.block_until_ready(k_tpm, timeout=token_timeout, rate=est_tokens)
    except Exception as exc:
        _record_limiter_infra_error("token", exc)
        token_response = None
    if token_response is not None and not token_response.allowed:
        retry_after = _retry_after_from_reset(token_response.reset)
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={"model_key": model_key, "kind": "tpm", "route": route, "retry_after_s": retry_after},
        )
        raise LlmRateLimited(kind="tpm", model_key=model_key, route=route, retry_after_s=retry_after)

    _record_limiter_infra_success()
