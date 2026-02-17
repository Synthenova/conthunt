from __future__ import annotations

import asyncio
import math
import random
import time
from collections import defaultdict
from typing import Any, Iterable

from app.core import get_settings, logger
from app.llm.context import get_llm_route
from app.llm.model_policy import canonicalize_model_key, resolve_model_limits
from app.integrations.posthog_client import capture_event


class LlmRateLimited(ValueError):
    """
    Raised when our global per-model limiter rejects a call.

    Subclasses ValueError so CloudTaskExecutor treats it as non-retryable.
    """

    def __init__(
        self,
        *,
        kind: str,  # "rpd" | "rpm" | "tpm" | "tpm_call_too_large" | "misconfigured"
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

    def __str__(self) -> str:
        # Preserve message formatting from __init__.
        return super().__str__()


def _is_background_route(route: str | None) -> bool:
    if not route:
        return False
    return route.startswith(("analysis.", "insights.", "tasks.", "deep_research.", "deep.research."))


def _safe_setattr(obj: Any, name: str, value: Any) -> None:
    try:
        setattr(obj, name, value)
    except Exception:
        # Some LangChain objects are Pydantic models; object.__setattr__ often works.
        try:
            object.__setattr__(obj, name, value)
        except Exception:
            # Best-effort only.
            pass


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
                    # Non-text blocks (images/media/etc). Add a conservative overhead.
                    # We can't reliably tokenize images; this is an envelope, not exact billing.
                    total += 1024
        return total
    if isinstance(content, dict):
        # Some providers/messages may embed nested content.
        return _extract_text_len_from_content(content.get("text") or content.get("content"))
    return len(str(content))


def estimate_tokens(messages: Any, *, completion_tokens_hint: int | None = None) -> int:
    """
    Cheap, provider-agnostic estimate.
    - Count input characters from message content -> tokens ~= chars/4
    - Add an estimated completion token budget.
    """
    settings = get_settings()

    # Normalize common shapes:
    # - list[BaseMessage] / list[dict]
    # - dict with "messages" key
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
        # Single message or string prompt
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
    est = max(1, in_tokens + max(0, out_tokens))
    return est


_THROTTLED_AVAILABLE: bool | None = None
_REDIS_STORE: Any | None = None
_LIMITER_COOLDOWN_UNTIL: float = 0.0
_LIMITER_INFRA_ERRORS: int = 0
_LIMITER_INFRA_LAST_LOG_AT: dict[str, float] = {}
_LIMITER_INFRA_SUPPRESSED: dict[str, int] = defaultdict(int)


def _ensure_throttled_loaded() -> bool:
    global _THROTTLED_AVAILABLE
    if _THROTTLED_AVAILABLE is not None:
        return _THROTTLED_AVAILABLE
    try:
        import throttled  # noqa: F401
    except Exception:
        logger.warning("[llm_rl] throttled is not installed; limiter is inactive until dependency is added")
        _THROTTLED_AVAILABLE = False
        return False
    _THROTTLED_AVAILABLE = True
    return True


def _build_limiters(*, rpm: int, tpm: int, rpd: int, tpm_burst: int):
    """
    Lazy construction so importing this module doesn't hard-require `throttled`
    before you freeze/install it.
    """
    if not _ensure_throttled_loaded():
        return None

    from throttled.asyncio import RateLimiterType, Throttled, rate_limiter

    redis_store = _get_redis_store()

    start = Throttled(
        using=RateLimiterType.GCRA.value,
        quota=rate_limiter.per_min(rpm, burst=1),
        store=redis_store,
    )
    tokens = Throttled(
        using=RateLimiterType.GCRA.value,
        quota=rate_limiter.per_min(tpm, burst=tpm_burst),
        store=redis_store,
    )
    daily = Throttled(
        using=RateLimiterType.FIXED_WINDOW.value,
        quota=rate_limiter.per_day(rpd),
        store=redis_store,
    )
    return start, tokens, daily


def _get_redis_store():
    """
    Build a single shared throttled RedisStore per process.
    This avoids creating multiple independent redis pools from the limiter path.
    """
    global _REDIS_STORE
    if _REDIS_STORE is not None:
        return _REDIS_STORE

    from throttled.asyncio import store

    settings = get_settings()
    # Dedicated limiter pool: small, bounded, blocking, and independent from main/stream pools.
    limiter_max_connections = max(1, int(settings.REDIS_LIMITER_MAX_CONNECTIONS))
    limiter_pool_timeout = max(0.1, float(settings.REDIS_LIMITER_POOL_TIMEOUT_S))
    options = {
        "REUSE_CONNECTION": True,
        "CONNECTION_POOL_CLASS": "redis.asyncio.BlockingConnectionPool",
        "CONNECTION_POOL_KWARGS": {
            "max_connections": limiter_max_connections,
            "timeout": limiter_pool_timeout,
            "socket_keepalive": True,
            "health_check_interval": 30,
            "client_name": "conthunt-llm-limiter",
        },
    }
    _REDIS_STORE = store.RedisStore(server=settings.REDIS_URL, options=options)
    return _REDIS_STORE


def _in_cooldown() -> bool:
    return time.monotonic() < _LIMITER_COOLDOWN_UNTIL


def _record_limiter_infra_error(stage: str, exc: Exception) -> None:
    global _LIMITER_INFRA_ERRORS, _LIMITER_COOLDOWN_UNTIL
    settings = get_settings()
    _LIMITER_INFRA_ERRORS += 1
    now = time.monotonic()

    # Activate short fail-open cooldown if we see a burst of infra errors.
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


_LIMITERS_BY_QUOTA: dict[tuple[int, int, int, int], tuple[Any, Any, Any]] = {}


def _get_limiters(*, rpm: int, tpm: int, rpd: int, tpm_burst: int) -> tuple[Any, Any, Any]:
    key = (int(rpm), int(tpm), int(rpd), int(tpm_burst))
    existing = _LIMITERS_BY_QUOTA.get(key)
    if existing is not None:
        return existing
    built = _build_limiters(rpm=key[0], tpm=key[1], rpd=key[2], tpm_burst=key[3])
    if built is None:
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={
                "model_key": "*",
                "kind": "misconfigured",
                "route": get_llm_route(),
            },
        )
        raise LlmRateLimited(
            kind="misconfigured_throttled_missing",
            model_key="*",
            route=get_llm_route(),
            retry_after_s=None,
        )
    _LIMITERS_BY_QUOTA[key] = built
    return built


async def enforce_model_global_limits(
    *,
    model_key: str,
    messages: Any,
    completion_tokens_hint: int | None = None,
) -> None:
    """
    Enforce per-model global limits (distributed via RedisStore).
    Order:
    1) RPD fail-fast
    2) RPM pacer (GCRA burst=1) with wait-and-retry
    3) Jitter
    4) TPM reservation with wait-and-retry
    """
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
    except LlmRateLimited:
        raise
    except Exception as exc:
        # Fail-open only for limiter infrastructure issues.
        _record_limiter_infra_error("init", exc)
        return

    k_rpd = f"rl:llm:global:model:{model_key}:rpd"
    k_start = f"rl:llm:global:model:{model_key}:start"
    k_tpm = f"rl:llm:global:model:{model_key}:tpm"

    # 0) Ensure call can ever pass the token limiter.
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

    # 1) Daily cap: fail-fast.
    try:
        # throttled expects non-blocking timeout as -1 (not 0).
        r = await daily_limiter.limit(k_rpd, cost=1, timeout=-1)
    except TypeError:
        # Some versions use positional args; keep compatibility.
        r = await daily_limiter.limit(k_rpd, cost=1)
    except Exception as exc:
        _record_limiter_infra_error("daily", exc)
        r = None
    if r is not None and getattr(r, "limited", False):
        state = getattr(r, "state", None)
        retry_after = getattr(state, "retry_after", None) if state is not None else None
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={
                "model_key": model_key,
                "kind": "rpd",
                "route": route,
                "retry_after_s": retry_after,
            },
        )
        raise LlmRateLimited(kind="rpd", model_key=model_key, route=route, retry_after_s=retry_after)

    # 2) Global start pacer: smooth system-wide thundering herd per model.
    try:
        r = await start_limiter.limit(k_start, cost=1, timeout=start_timeout)
    except Exception as exc:
        _record_limiter_infra_error("start", exc)
        r = None
    if r is not None and getattr(r, "limited", False):
        state = getattr(r, "state", None)
        retry_after = getattr(state, "retry_after", None) if state is not None else None
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={
                "model_key": model_key,
                "kind": "rpm",
                "route": route,
                "retry_after_s": retry_after,
            },
        )
        raise LlmRateLimited(kind="rpm", model_key=model_key, route=route, retry_after_s=retry_after)

    # Avoid same-ms wakeups for many waiting tasks.
    await asyncio.sleep(random.uniform(0, 0.05))

    # 3) Token fairness: reserve est tokens before starting the call.
    try:
        r = await token_limiter.limit(k_tpm, cost=est_tokens, timeout=token_timeout)
    except Exception as exc:
        _record_limiter_infra_error("token", exc)
        r = None
    if r is not None and getattr(r, "limited", False):
        state = getattr(r, "state", None)
        retry_after = getattr(state, "retry_after", None) if state is not None else None
        capture_event(
            distinct_id="system:rate_limit",
            event="llm_rate_limited",
            properties={
                "model_key": model_key,
                "kind": "tpm",
                "route": route,
                "retry_after_s": retry_after,
            },
        )
        raise LlmRateLimited(kind="tpm", model_key=model_key, route=route, retry_after_s=retry_after)
    _record_limiter_infra_success()
