"""Global rate limiter for LLM API calls.

Uses Redis Lua scripts to implement an atomic sliding window rate limiter
that works across all Cloud Run instances with minimal connections.
"""
import asyncio
import time
from typing import Optional

import redis.asyncio as redis

from app.core import logger

# Requests per minute limits per model
MODEL_RATE_LIMITS: dict[str, int] = {
    # Google models
    "google/gemini-3-flash-preview": 1000,
    "google/gemini-3-pro-preview": 25,
    # Default for all OpenRouter models
    "__default__": 500,
}

# Lua script for atomic rate limit check and acquire
# Returns: 1 if acquired, 0 if rate limited, -1 with wait time hint
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local request_id = ARGV[4]
local window_seconds = tonumber(ARGV[5])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

-- Count current requests in window
local count = redis.call('ZCARD', key)

if count < limit then
    -- We have capacity - add this request
    redis.call('ZADD', key, now, request_id)
    redis.call('EXPIRE', key, window_seconds + 10)
    return {1, count + 1}  -- success, new count
end

-- Over limit - get oldest entry to calculate wait time
local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local wait_hint = 1
if oldest and #oldest >= 2 then
    local oldest_ts = tonumber(oldest[2])
    wait_hint = math.max(1, (oldest_ts + window_seconds) - now)
end

return {0, wait_hint}  -- rate limited, wait time hint
"""


class ModelRateLimiter:
    """
    Redis-backed sliding window rate limiter for LLM API calls.
    
    Uses a Lua script to perform all operations atomically in a single
    Redis round-trip, minimizing connection usage.
    
    Key format: "ratelimit:model:{model_name}"
    """

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._script = None  # Lazy-loaded Lua script

    async def _get_script(self):
        """Lazily register the Lua script with Redis."""
        if self._script is None:
            self._script = self._redis.register_script(RATE_LIMIT_SCRIPT)
        return self._script

    def _get_limit(self, model_name: str) -> int:
        """Get RPM limit for a model, falling back to default."""
        return MODEL_RATE_LIMITS.get(model_name, MODEL_RATE_LIMITS["__default__"])

    async def acquire(
        self,
        model_name: str,
        timeout: float = 30.0,
    ) -> bool:
        """
        Wait until rate limit allows the request, or raise after timeout.
        
        Uses a single Redis Lua script call per attempt for efficiency.
        
        Args:
            model_name: Full model name (e.g., "google/gemini-3-flash-preview")
            timeout: Max seconds to wait before raising RuntimeError
            
        Returns:
            True if acquired successfully
            
        Raises:
            RuntimeError: If timeout exceeded waiting for rate limit
        """
        limit = self._get_limit(model_name)
        key = f"ratelimit:model:{model_name}"
        window_seconds = 60

        deadline = time.monotonic() + timeout
        attempt = 0

        try:
            script = await self._get_script()
        except redis.RedisError as e:
            logger.warning("Redis error registering rate limit script: %s", e)
            return True  # Fail open

        while time.monotonic() < deadline:
            now = int(time.time())
            window_start = now - window_seconds
            request_id = f"{now}:{id(asyncio.current_task())}:{attempt}"

            try:
                # Single atomic Lua script call - uses only 1 connection!
                result = await script(
                    keys=[key],
                    args=[limit, window_start, now, request_id, window_seconds],
                )

                success = result[0]
                
                if success == 1:
                    if attempt > 0:
                        new_count = result[1]
                        logger.debug(
                            "Rate limit acquired for %s after %d retries (count=%d/%d)",
                            model_name, attempt, new_count, limit
                        )
                    return True

                # Rate limited - use wait hint from script
                wait_hint = result[1]
                wait_time = min(max(0.5, wait_hint), 2.0)  # Clamp to 0.5-2s

                logger.info(
                    "Rate limit hit for %s (limit=%d), waiting %.1fs",
                    model_name, limit, wait_time
                )
                await asyncio.sleep(wait_time)
                attempt += 1

            except redis.RedisError as e:
                logger.warning("Redis error in rate limiter: %s", e)
                # On Redis failure, allow the request (fail open)
                return True

        raise RuntimeError(
            f"Rate limit timeout for model {model_name} after {timeout}s "
            f"(limit: {limit} req/min)"
        )

    async def get_usage(self, model_name: str) -> tuple[int, int]:
        """
        Get current usage for a model.
        
        Returns:
            Tuple of (current_count, limit)
        """
        limit = self._get_limit(model_name)
        key = f"ratelimit:model:{model_name}"
        now = int(time.time())
        window_start = now - 60

        try:
            # Use pipeline to reduce to 1 connection
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                results = await pipe.execute()
            return (results[1], limit)
        except redis.RedisError:
            return (0, limit)


# Singleton instance - initialized lazily with Redis client
_limiter_instance: Optional[ModelRateLimiter] = None


def get_rate_limiter(redis_client: redis.Redis) -> ModelRateLimiter:
    """Get or create the global rate limiter instance."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = ModelRateLimiter(redis_client)
    return _limiter_instance
