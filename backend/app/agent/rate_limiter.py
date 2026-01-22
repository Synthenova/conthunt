"""Global rate limiter for LLM API calls.

Uses Redis sorted sets to implement a sliding window rate limiter
that works across all Cloud Run instances.
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


class ModelRateLimiter:
    """
    Redis-backed sliding window rate limiter for LLM API calls.
    
    Uses sorted sets where:
    - Key = "ratelimit:model:{model_name}"
    - Members = unique request IDs
    - Scores = Unix timestamps
    
    This allows true sliding window limiting across distributed instances.
    """

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

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

        while time.monotonic() < deadline:
            now = int(time.time())
            window_start = now - window_seconds
            request_id = f"{now}:{id(asyncio.current_task())}:{attempt}"

            try:
                # Atomic pipeline: cleanup old entries + count current
                async with self._redis.pipeline(transaction=True) as pipe:
                    pipe.zremrangebyscore(key, 0, window_start)
                    pipe.zcard(key)
                    results = await pipe.execute()

                current_count = results[1]

                if current_count < limit:
                    # We have capacity - add this request
                    await self._redis.zadd(key, {request_id: now})
                    await self._redis.expire(key, window_seconds + 10)
                    
                    if attempt > 0:
                        logger.debug(
                            "Rate limit acquired for %s after %d retries (count=%d/%d)",
                            model_name, attempt, current_count + 1, limit
                        )
                    return True

                # Over limit - calculate wait time
                # Get oldest entry to estimate when slot opens
                oldest = await self._redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_ts = int(oldest[0][1])
                    wait_time = max(0.5, (oldest_ts + window_seconds) - now + 0.1)
                    wait_time = min(wait_time, 2.0)  # Cap at 2s per retry
                else:
                    wait_time = 0.5

                logger.debug(
                    "Rate limit hit for %s (count=%d/%d), waiting %.1fs",
                    model_name, current_count, limit, wait_time
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
            await self._redis.zremrangebyscore(key, 0, window_start)
            count = await self._redis.zcard(key)
            return (count, limit)
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
