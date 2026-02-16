from __future__ import annotations

import redis.asyncio as redis
from fastapi import Request

from app.core import get_settings

_global_redis: redis.Redis | None = None


def get_redis_from_state(state) -> redis.Redis:
    client = getattr(state, "redis", None)
    if client is None:
        raise RuntimeError("Redis client is not initialized on app.state")
    return client


def get_app_redis(request: Request) -> redis.Redis:
    return get_redis_from_state(request.app.state)


def get_global_redis() -> redis.Redis:
    """
    Prefer the app-scoped Redis client (app.state.redis) when available to avoid
    creating multiple pools per process (which increases idle sockets and
    connection-limit pressure under SSE).
    """
    global _global_redis
    try:
        # Lazily import to avoid import cycles at module import time.
        from app.main import app as main_app  # type: ignore

        state_client = getattr(getattr(main_app, "state", None), "redis", None)
        if state_client is not None:
            return state_client
    except Exception:
        # Fall back to a standalone global client below.
        pass

    if _global_redis is None:
        settings = get_settings()
        from redis.asyncio.connection import BlockingConnectionPool

        pool = BlockingConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAIN_MAX_CONNECTIONS,
            timeout=settings.REDIS_MAIN_POOL_TIMEOUT_S,
            decode_responses=True,
            health_check_interval=30,
            socket_keepalive=True,
            client_name="conthunt-main-fallback",
        )
        _global_redis = redis.Redis(connection_pool=pool)
    return _global_redis
