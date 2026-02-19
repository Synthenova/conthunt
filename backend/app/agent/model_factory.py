"""Model initialization factory for chat models."""
from typing import Any, Iterable, Tuple
from functools import wraps
import httpx

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core import get_settings, logger
from app.integrations.posthog_client import capture_event_with_error
from app.llm.context import get_llm_route, get_llm_user_id
from app.llm.global_rate_limiter import LlmRateLimited, enforce_model_global_limits
from app.llm.model_policy import canonicalize_model_key, get_model_fallback_chain

DEFAULT_MODEL_NAME = "openrouter/google/gemini-3-flash-preview"
SUPPORTED_PROVIDERS = {"openrouter", "google", "google-vertex", "google-api"}

# Model options - keep in sync with frontend/src/components/chat/chat-input/constants.ts
MODEL_OPTIONS = [
    {"label": "Grok 4.1 Fast (xAI)", "value": "openrouter/x-ai/grok-4.1-fast"},
    {"label": "Gemini 3 Flash", "value": "openrouter/google/gemini-3-flash-preview"},    
    {"label": "MiMo-V2-Flash (Xiaomi, free)", "value": "openrouter/xiaomi/mimo-v2-flash:free"},
    {"label": "GPT-5.2 (OpenAI)", "value": "openrouter/openai/gpt-5.2"},
    {"label": "GPT-5.1 (OpenAI)", "value": "openrouter/openai/gpt-5.1"},
    {"label": "DeepSeek V3.2 (DeepSeek)", "value": "openrouter/deepseek/deepseek-v3.2"},
    {"label": "Mistral Small Creative (Mistral)", "value": "openrouter/mistralai/mistral-small-creative"},
]

ALLOWED_MODEL_VALUES = frozenset(opt["value"] for opt in MODEL_OPTIONS)


def _parse_model_name(model_name: str | None) -> Tuple[str, str]:
    if not model_name:
        model_name = DEFAULT_MODEL_NAME

    if "/" not in model_name:
        return "google", model_name

    provider, remainder = model_name.split("/", 1)
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported model provider: {provider}")
    if not remainder:
        raise ValueError("Model name missing after provider prefix.")

    return provider, remainder


def _canonical_provider(provider: str) -> str:
    if provider == "google":
        return "google-vertex"
    return provider


def _model_key_from_name(model_name: str | None) -> str:
    provider, resolved_name = _parse_model_name(model_name)
    return canonicalize_model_key(f"{_canonical_provider(provider)}/{resolved_name}")


def _create_google_api_model(*, resolved_name: str, temperature: float):
    settings = get_settings()
    kwargs = {
        "model": resolved_name,
        "temperature": temperature,
        "max_retries": 1,
    }
    if settings.GOOGLE_API_KEY:
        kwargs["google_api_key"] = settings.GOOGLE_API_KEY
    try:
        return ChatGoogleGenerativeAI(**kwargs)
    except TypeError:
        kwargs.pop("google_api_key", None)
        if settings.GOOGLE_API_KEY:
            kwargs["api_key"] = settings.GOOGLE_API_KEY
        return ChatGoogleGenerativeAI(**kwargs)


def _create_base_model_from_key(
    model_key: str,
    temperature: float,
    llm_init_kwargs: dict[str, Any] | None = None,
):
    settings = get_settings()
    provider, resolved_name = _parse_model_name(model_key)
    provider = _canonical_provider(provider)
    llm_init_kwargs = dict(llm_init_kwargs or {})

    if provider == "openrouter":
        base_kwargs: dict[str, Any] = {
            "model": resolved_name,
            "temperature": temperature,
            "base_url": settings.OPENAI_BASE_URL,
            "api_key": settings.OPENAI_API_KEY,
            "max_retries": 0,
        }
        base_kwargs.update(llm_init_kwargs)
        return ChatOpenAI(**base_kwargs)

    if provider == "google-api":
        return _create_google_api_model(resolved_name=resolved_name, temperature=temperature)

    base_kwargs = {
        "model": resolved_name,
        "temperature": temperature,
        "project": settings.GCP_PROJECT,
        "vertexai": True,
        "max_retries": 1,
        "location": "global",
    }
    base_kwargs.update(llm_init_kwargs)
    return ChatGoogleGenerativeAI(**base_kwargs)


def init_chat_model(
    model_name: str | None,
    temperature: float = 0.5,
    llm_init_kwargs: dict[str, Any] | None = None,
):
    model_key = _model_key_from_name(model_name)
    llm = _create_base_model_from_key(
        model_key,
        temperature=temperature,
        llm_init_kwargs=llm_init_kwargs,
    )
    return _attach_global_llm_limits(
        llm,
        model_key=model_key,
        temperature=temperature,
        llm_init_kwargs=llm_init_kwargs,
    )


def _extract_completion_tokens_hint(kwargs: dict) -> int | None:
    # Common conventions across providers / wrappers.
    for k in ("max_output_tokens", "max_tokens", "max_completion_tokens"):
        v = kwargs.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except Exception:
            return None
    return None


def _mark_wrapped(obj: Any) -> bool:
    """
    Return True if we successfully marked the object as wrapped.
    If attribute setting is blocked, we still proceed without the marker (best effort).
    """
    try:
        if getattr(obj, "__conthunt_rl_wrapped__", False):
            return True
        setattr(obj, "__conthunt_rl_wrapped__", True)
        return True
    except Exception:
        try:
            if getattr(obj, "__conthunt_rl_wrapped__", False):
                return True
        except Exception:
            pass
        return False


def _safe_setattr(obj: Any, name: str, value: Any) -> None:
    try:
        setattr(obj, name, value)
    except Exception:
        try:
            object.__setattr__(obj, name, value)
        except Exception:
            pass


def _is_internal_rate_limit(exc: Exception) -> bool:
    if not isinstance(exc, LlmRateLimited):
        return False
    return exc.kind in {"rpd", "rpm", "tpm"}


def _is_upstream_429(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return int(exc.response.status_code) == 429
        except Exception:
            return False
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        try:
            return int(status_code) == 429
        except Exception:
            pass
    response = getattr(exc, "response", None)
    if response is not None:
        resp_code = getattr(response, "status_code", None)
        if resp_code is not None:
            try:
                return int(resp_code) == 429
            except Exception:
                pass
    return False


def _should_switch_on_error(exc: Exception) -> bool:
    return _is_internal_rate_limit(exc) or _is_upstream_429(exc)


def _extract_status_code(exc: Exception) -> int | None:
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        try:
            return int(status_code)
        except Exception:
            pass
    response = getattr(exc, "response", None)
    if response is not None:
        resp_code = getattr(response, "status_code", None)
        if resp_code is not None:
            try:
                return int(resp_code)
            except Exception:
                pass
    return None


def _capture_llm_exception_event(
    *,
    exc: Exception,
    model_key: str,
    attempt: int,
    max_attempts: int,
    mode: str,
    event: str,
    switch_eligible: bool,
) -> None:
    capture_event_with_error(
        distinct_id=get_llm_user_id() or "system:llm_fallback",
        event=event,
        exception=exc,
        properties={
            "model_key": model_key,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "mode": mode,
            "status_code": _extract_status_code(exc),
            "is_internal_rate_limit": _is_internal_rate_limit(exc),
            "switch_eligible": switch_eligible,
            "route": get_llm_route(),
        },
    )


def _build_attempt_runnable(
    *,
    model_key: str,
    temperature: float,
    transforms: list[tuple[str, tuple[Any, ...], dict[str, Any]]],
    llm_init_kwargs: dict[str, Any] | None = None,
):
    runnable = _create_base_model_from_key(
        model_key,
        temperature=temperature,
        llm_init_kwargs=llm_init_kwargs,
    )
    for method_name, args, kwargs in transforms:
        method = getattr(runnable, method_name)
        runnable = method(*args, **kwargs)
    return runnable


def _attach_global_llm_limits(
    obj: Any,
    *,
    model_key: str,
    temperature: float,
    transforms: list[tuple[str, tuple[Any, ...], dict[str, Any]]] | None = None,
    llm_init_kwargs: dict[str, Any] | None = None,
):
    """
    Attach per-model global rate limiting to the runnable/model instance.

    We wrap instance methods (ainvoke/astream + bind_tools/with_structured_output)
    so downstream transformations keep the limiter.
    """
    if obj is None:
        return obj
    model_key = canonicalize_model_key(model_key)
    transforms = list(transforms or [])
    llm_init_kwargs = dict(llm_init_kwargs or {})

    # Avoid double wrapping when possible.
    try:
        if getattr(obj, "__conthunt_rl_wrapped__", False):
            return obj
    except Exception:
        pass

    _mark_wrapped(obj)
    _safe_setattr(obj, "__conthunt_model_key__", model_key)
    _safe_setattr(obj, "__conthunt_model_temperature__", temperature)
    _safe_setattr(obj, "__conthunt_model_transforms__", transforms)
    _safe_setattr(obj, "__conthunt_model_init_kwargs__", llm_init_kwargs)

    # Wrap async invoke
    if hasattr(obj, "ainvoke"):
        orig_ainvoke = getattr(obj, "ainvoke")

        @wraps(orig_ainvoke)
        async def _ainvoke_limited(input, *args, **kwargs):
            hint = _extract_completion_tokens_hint(kwargs)
            chain = get_model_fallback_chain(model_key)
            last_rate_limit_exc: Exception | None = None
            for idx, attempt_key in enumerate(chain):
                try:
                    await enforce_model_global_limits(
                        model_key=attempt_key,
                        messages=input,
                        completion_tokens_hint=hint,
                    )
                    if idx == 0:
                        return await orig_ainvoke(input, *args, **kwargs)
                    fallback_obj = _build_attempt_runnable(
                        model_key=attempt_key,
                        temperature=temperature,
                        transforms=transforms,
                        llm_init_kwargs=llm_init_kwargs,
                    )
                    return await fallback_obj.ainvoke(input, *args, **kwargs)
                except Exception as exc:
                    if _should_switch_on_error(exc):
                        _capture_llm_exception_event(
                            exc=exc,
                            model_key=attempt_key,
                            attempt=idx + 1,
                            max_attempts=len(chain),
                            mode="ainvoke",
                            event="llm_fallback_triggered",
                            switch_eligible=True,
                        )
                        last_rate_limit_exc = exc
                        logger.warning(
                            "[llm_fallback] switching model attempt=%s/%s from=%s to_next reason=%s",
                            idx + 1,
                            len(chain),
                            attempt_key,
                            type(exc).__name__,
                        )
                        continue
                    raise
            if last_rate_limit_exc is not None:
                raise last_rate_limit_exc
            raise RuntimeError(f"LLM fallback chain exhausted without result for model={model_key}")

        try:
            _safe_setattr(obj, "ainvoke", _ainvoke_limited)
        except Exception:
            pass

    # Wrap async stream
    if hasattr(obj, "astream"):
        orig_astream = getattr(obj, "astream")

        @wraps(orig_astream)
        async def _astream_limited(input, *args, **kwargs):
            hint = _extract_completion_tokens_hint(kwargs)
            chain = get_model_fallback_chain(model_key)
            last_rate_limit_exc: Exception | None = None
            for idx, attempt_key in enumerate(chain):
                try:
                    await enforce_model_global_limits(
                        model_key=attempt_key,
                        messages=input,
                        completion_tokens_hint=hint,
                    )
                    if idx == 0:
                        async for chunk in orig_astream(input, *args, **kwargs):
                            yield chunk
                        return
                    fallback_obj = _build_attempt_runnable(
                        model_key=attempt_key,
                        temperature=temperature,
                        transforms=transforms,
                        llm_init_kwargs=llm_init_kwargs,
                    )
                    async for chunk in fallback_obj.astream(input, *args, **kwargs):
                        yield chunk
                    return
                except Exception as exc:
                    should_switch = _should_switch_on_error(exc)
                    _capture_llm_exception_event(
                        exc=exc,
                        model_key=attempt_key,
                        attempt=idx + 1,
                        max_attempts=len(chain),
                        mode="astream",
                        event="llm_stream_exception",
                        switch_eligible=should_switch,
                    )
                    if should_switch:
                        last_rate_limit_exc = exc
                        logger.warning(
                            "[llm_fallback] switching stream attempt=%s/%s from=%s to_next reason=%s",
                            idx + 1,
                            len(chain),
                            attempt_key,
                            type(exc).__name__,
                        )
                        continue
                    raise
            if last_rate_limit_exc is not None:
                raise last_rate_limit_exc
            raise RuntimeError(f"LLM fallback stream chain exhausted without result for model={model_key}")

        try:
            _safe_setattr(obj, "astream", _astream_limited)
        except Exception:
            pass

    # Preserve wrapper across common LangChain transformations.
    for method_name in ("bind_tools", "with_structured_output"):
        if not hasattr(obj, method_name):
            continue
        orig = getattr(obj, method_name)

        @wraps(orig)
        def _wrapped(*args, __orig=orig, __method_name=method_name, **kwargs):
            res = __orig(*args, **kwargs)
            next_transforms = [*transforms, (__method_name, args, dict(kwargs))]
            return _attach_global_llm_limits(
                res,
                model_key=model_key,
                temperature=temperature,
                transforms=next_transforms,
                llm_init_kwargs=llm_init_kwargs,
            )

        try:
            _safe_setattr(obj, method_name, _wrapped)
        except Exception:
            pass

    return obj


def get_model_provider(model_name: str | None) -> str:
    provider, _ = _parse_model_name(model_name)
    provider = _canonical_provider(provider)
    if provider in {"google-vertex", "google-api"}:
        return "google"
    return provider


def _normalize_content_blocks(content: Any, target_provider: str) -> Any:
    if not isinstance(content, list):
        return content

    normalized = []
    for block in content:
        if not isinstance(block, dict):
            normalized.append(block)
            continue

        block_type = block.get("type")
        if target_provider == "google" and block_type == "image_url":
            url = (block.get("image_url") or {}).get("url") or block.get("url")
            if url:
                normalized.append({"type": "image", "url": url})
                continue
        if target_provider == "openrouter" and block_type == "image":
            url = block.get("url") or (block.get("image_url") or {}).get("url")
            if url:
                normalized.append({"type": "image_url", "image_url": {"url": url}})
                continue

        normalized.append(block)

    return normalized


def _copy_message_with_content(message: Any, content: Any) -> Any:
    if hasattr(message, "model_copy"):
        return message.model_copy(update={"content": content})
    if hasattr(message, "copy"):
        try:
            return message.copy(update={"content": content})
        except TypeError:
            pass
    if hasattr(message, "__class__"):
        try:
            data = dict(message.__dict__)
            data["content"] = content
            return message.__class__(**data)
        except Exception:
            pass
    try:
        setattr(message, "content", content)
    except Exception:
        return message
    return message


def normalize_messages_for_provider(
    messages: Iterable[Any],
    model_name: str | None,
) -> list[Any]:
    provider = get_model_provider(model_name)
    normalized_messages: list[Any] = []

    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content")
            normalized = _normalize_content_blocks(content, provider)
            if normalized is not content:
                updated = dict(msg)
                updated["content"] = normalized
                normalized_messages.append(updated)
            else:
                normalized_messages.append(msg)
            continue

        content = getattr(msg, "content", None)
        normalized = _normalize_content_blocks(content, provider)
        if normalized is content:
            normalized_messages.append(msg)
        else:
            normalized_messages.append(_copy_message_with_content(msg, normalized))

    return normalized_messages


async def init_chat_model_rated(
    model_name: str | None,
    redis_client,
    temperature: float = 0.5,
    timeout: float = 30.0,
):
    """
    Initialize a chat model (kept for API compatibility).
    
    Args:
        model_name: Full model name (e.g., "openrouter/google/gemini-3-flash-preview")
        redis_client: Unused (kept for API compatibility)
        temperature: Model temperature
        timeout: Unused (kept for API compatibility)
        
    Returns:
        Initialized chat model
    """
    # Keep parameters for callers that still pass them.
    _ = redis_client
    _ = timeout
    return init_chat_model(model_name, temperature=temperature)
