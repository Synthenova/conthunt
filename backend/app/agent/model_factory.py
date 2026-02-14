"""Model initialization factory for chat models."""
import os
from typing import Any, Iterable, Optional, Tuple
from functools import wraps

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core import get_settings
from app.llm.global_rate_limiter import enforce_model_global_limits

DEFAULT_MODEL_NAME = "openrouter/google/gemini-3-flash-preview"
SUPPORTED_PROVIDERS = {"openrouter", "google"}

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


def init_chat_model(model_name: str | None, temperature: float = 0.5):
    provider, resolved_name = _parse_model_name(model_name)
    settings = get_settings()
    model_key = f"{provider}/{resolved_name}"

    if provider == "openrouter":        
        llm = ChatOpenAI(
            model=resolved_name,
            temperature=temperature,
            openai_api_base=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            max_retries=1            
        )
        return _attach_global_llm_limits(llm, model_key=model_key)

    llm = ChatGoogleGenerativeAI(
        model=resolved_name,
        temperature=temperature,
        project=settings.GCP_PROJECT,
        vertexai=True,
        max_retries=1,
        location='global'        
    )
    return _attach_global_llm_limits(llm, model_key=model_key)


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


def _attach_global_llm_limits(obj: Any, *, model_key: str):
    """
    Attach per-model global rate limiting to the runnable/model instance.

    We wrap instance methods (ainvoke/astream + bind_tools/with_structured_output)
    so downstream transformations keep the limiter.
    """
    if obj is None:
        return obj

    # Avoid double wrapping when possible.
    try:
        if getattr(obj, "__conthunt_rl_wrapped__", False):
            return obj
    except Exception:
        pass

    _mark_wrapped(obj)

    # Wrap async invoke
    if hasattr(obj, "ainvoke"):
        orig_ainvoke = getattr(obj, "ainvoke")

        @wraps(orig_ainvoke)
        async def _ainvoke_limited(input, *args, **kwargs):
            hint = _extract_completion_tokens_hint(kwargs)
            await enforce_model_global_limits(model_key=model_key, messages=input, completion_tokens_hint=hint)
            return await orig_ainvoke(input, *args, **kwargs)

        try:
            setattr(obj, "ainvoke", _ainvoke_limited)
        except Exception:
            pass

    # Wrap async stream
    if hasattr(obj, "astream"):
        orig_astream = getattr(obj, "astream")

        @wraps(orig_astream)
        async def _astream_limited(input, *args, **kwargs):
            hint = _extract_completion_tokens_hint(kwargs)
            await enforce_model_global_limits(model_key=model_key, messages=input, completion_tokens_hint=hint)
            async for chunk in orig_astream(input, *args, **kwargs):
                yield chunk

        try:
            setattr(obj, "astream", _astream_limited)
        except Exception:
            pass

    # Preserve wrapper across common LangChain transformations.
    for method_name in ("bind_tools", "with_structured_output"):
        if not hasattr(obj, method_name):
            continue
        orig = getattr(obj, method_name)

        @wraps(orig)
        def _wrapped(*args, __orig=orig, **kwargs):
            res = __orig(*args, **kwargs)
            return _attach_global_llm_limits(res, model_key=model_key)

        try:
            setattr(obj, method_name, _wrapped)
        except Exception:
            pass

    return obj


def get_model_provider(model_name: str | None) -> str:
    provider, _ = _parse_model_name(model_name)
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
