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
    global _global_redis
    if _global_redis is None:
        settings = get_settings()
        from redis.asyncio.connection import BlockingConnectionPool

        pool = BlockingConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            timeout=10.0,
            decode_responses=True,
        )
        _global_redis = redis.Redis(connection_pool=pool)
    return _global_redis
