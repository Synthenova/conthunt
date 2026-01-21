from __future__ import annotations

import redis.asyncio as redis
from fastapi import Request


def get_redis_from_state(state) -> redis.Redis:
    client = getattr(state, "redis", None)
    if client is None:
        raise RuntimeError("Redis client is not initialized on app.state")
    return client


def get_app_redis(request: Request) -> redis.Redis:
    return get_redis_from_state(request.app.state)
