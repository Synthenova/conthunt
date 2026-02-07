from __future__ import annotations

from typing import Any, AsyncIterator

from app.llm.gateway import get_gateway, init_gateway
from app.core.redis_client import get_global_redis


class RateLimitedChatModel:
    def __init__(self, inner: Any, limiter: Any, full_model_name: str):
        self._inner = inner
        self._model_name = full_model_name
        self._limiter = limiter

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def bind_tools(self, tools: Any, **kwargs: Any) -> "RateLimitedChatModel":
        bound = self._inner.bind_tools(tools, **kwargs)
        return RateLimitedChatModel(bound, self._limiter, self._model_name)

    def with_structured_output(self, *args: Any, **kwargs: Any) -> "RateLimitedRunnable":
        bound = self._inner.with_structured_output(*args, **kwargs)
        return RateLimitedRunnable(bound, self._limiter, self._model_name)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        user_id, route = _extract_user_route(args, kwargs)
        limiter = self._limiter or _ensure_gateway()
        return await limiter.run_invoke(
            self._model_name,
            user_id,
            route,
            self._inner.ainvoke,
            *args,
            **kwargs,
        )

    async def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        user_id, route = _extract_user_route(args, kwargs)
        limiter = self._limiter or _ensure_gateway()
        stream = await limiter.run_stream(
            self._model_name,
            user_id,
            route,
            self._inner.astream,
            *args,
            **kwargs,
        )
        async for item in stream:
            yield item

    async def agenerate(self, *args: Any, **kwargs: Any) -> Any:
        user_id, route = _extract_user_route(args, kwargs)
        limiter = self._limiter or _ensure_gateway()
        return await limiter.run_invoke(
            self._model_name,
            user_id,
            route,
            self._inner.agenerate,
            *args,
            **kwargs,
        )


class RateLimitedRunnable:
    def __init__(self, inner: Any, limiter: Any, full_model_name: str):
        self._inner = inner
        self._model_name = full_model_name
        self._limiter = limiter

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        user_id, route = _extract_user_route(args, kwargs)
        limiter = self._limiter or _ensure_gateway()
        return await limiter.run_invoke(
            self._model_name,
            user_id,
            route,
            self._inner.ainvoke,
            *args,
            **kwargs,
        )

    async def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        user_id, route = _extract_user_route(args, kwargs)
        limiter = self._limiter or _ensure_gateway()
        stream = await limiter.run_stream(
            self._model_name,
            user_id,
            route,
            self._inner.astream,
            *args,
            **kwargs,
        )
        async for item in stream:
            yield item

    async def agenerate(self, *args: Any, **kwargs: Any) -> Any:
        user_id, route = _extract_user_route(args, kwargs)
        limiter = self._limiter or _ensure_gateway()
        return await limiter.run_invoke(
            self._model_name,
            user_id,
            route,
            self._inner.agenerate,
            *args,
            **kwargs,
        )


def _extract_user_route(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[str | None, str | None]:
    config = kwargs.get("config")
    if config is None and len(args) >= 2 and isinstance(args[1], dict):
        config = args[1]
    user_id = None
    route = None
    if isinstance(config, dict):
        configurable = config.get("configurable") or {}
        user_id = configurable.get("user_id")
        route = configurable.get("llm_route") or configurable.get("route")
    return user_id, route


def _ensure_gateway():
    try:
        return get_gateway()
    except RuntimeError:
        return init_gateway(get_global_redis())
