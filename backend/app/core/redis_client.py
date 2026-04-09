from __future__ import annotations

from fastapi import Request
from upstash_redis.asyncio import Redis

_global_redis: Redis | None = None


def get_redis_from_state(state) -> Redis:
    client = getattr(state, "redis", None)
    if client is None:
        raise RuntimeError("Redis client is not initialized on app.state")
    return client


def get_app_redis(request: Request) -> Redis:
    return get_redis_from_state(request.app.state)


def get_global_redis() -> Redis:
    global _global_redis
    try:
        from app.main import app as main_app  # type: ignore

        state_client = getattr(getattr(main_app, "state", None), "redis", None)
        if state_client is not None:
            return state_client
    except Exception:
        pass

    if _global_redis is None:
        _global_redis = Redis.from_env(read_your_writes=True)
    return _global_redis
