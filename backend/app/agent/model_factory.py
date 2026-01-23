"""Model initialization factory for chat models."""
import os
from typing import Any, Iterable, Optional, Tuple

import redis.asyncio as redis
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core import get_settings
from app.agent.rate_limiter import get_rate_limiter

DEFAULT_MODEL_NAME = "google/gemini-3-flash-preview"
SUPPORTED_PROVIDERS = {"openrouter", "google"}

# Model options - keep in sync with frontend/src/components/chat/chat-input/constants.ts
MODEL_OPTIONS = [
    {"label": "Gemini 3 Flash", "value": "google/gemini-3-flash-preview"},    
    {"label": "Grok 4.1 Fast (xAI)", "value": "openrouter/x-ai/grok-4.1-fast"},
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

    if provider == "openrouter":        
        return ChatOpenAI(
            model=resolved_name,
            temperature=temperature,
            openai_api_base=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
        )

    return ChatGoogleGenerativeAI(
        model=resolved_name,
        temperature=temperature,
        project=settings.GCLOUD_PROJECT,
        vertexai=True,
    )


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
    redis_client: redis.Redis,
    temperature: float = 0.5,
    timeout: float = 30.0,
):
    """
    Initialize a chat model with rate limiting.
    
    Acquires a rate limit slot before returning the model.
    Use this for all LLM calls to ensure global rate limits are respected.
    
    Args:
        model_name: Full model name (e.g., "google/gemini-3-flash-preview")
        redis_client: Redis client for rate limiting
        temperature: Model temperature
        timeout: Max seconds to wait for rate limit
        
    Returns:
        Initialized chat model
        
    Raises:
        RuntimeError: If rate limit acquisition times out
    """
    # Normalize model name for rate limiting
    if not model_name:
        model_name = DEFAULT_MODEL_NAME
    
    # Acquire rate limit slot
    limiter = get_rate_limiter(redis_client)
    await limiter.acquire(model_name, timeout=timeout)
    
    # Return the model
    return init_chat_model(model_name, temperature=temperature)

