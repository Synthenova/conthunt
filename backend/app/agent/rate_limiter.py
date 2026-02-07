"""Global rate limiter for LLM API calls.

Implements:
- RPM smoothing via request token bucket (sub-second spread)
- RPM/RPD absolute caps via sliding window
- TPM absolute cap via sliding window (token sums)
"""
import asyncio
import random
import time
from typing import Optional

import redis.asyncio as redis

from app.core import logger

# Requests per minute limits per model
MODEL_RATE_LIMITS: dict[str, int] = {
    # Google models
    "openrouter/google/gemini-3-flash-preview": 500,
    "openrouter/google/gemini-3-pro-preview": 25,
    # Default for all OpenRouter models
    "__default__": 500,
}

# Tokens per minute limits per model
MODEL_TPM_LIMITS: dict[str, int] = {
    "openrouter/google/gemini-3-flash-preview": 1_000_000,
    "openrouter/google/gemini-3-pro-preview": 1_000_000,
    "__default__": 1_000_000,  # OpenRouter + others follow Flash
}

# Requests per day limits per model (global only)
MODEL_RPD_LIMITS: dict[str, int] = {
    "openrouter/google/gemini-3-flash-preview": 10_000,
    "openrouter/google/gemini-3-pro-preview": 250,
    "__default__": 10_000,
}

# Request burst smoothing (sub-second)
RPM_BURST_SECONDS = 1

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

# Lua script for RPM smoothing + absolute cap
# Returns:
# {1, remaining_tokens} on success
# {0, wait_ms} if bucket is empty
# {-1, wait_seconds} if RPM window is full
RPM_COMBINED_SCRIPT = """
local bucket_key = KEYS[1]
local window_key = KEYS[2]

local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now_ms = tonumber(ARGV[3])
local limit = tonumber(ARGV[4])
local window_start = tonumber(ARGV[5])
local now = tonumber(ARGV[6])
local request_id = ARGV[7]
local window_seconds = tonumber(ARGV[8])

-- Bucket refill
local data = redis.call("HMGET", bucket_key, "tokens", "ts")
local tokens = tonumber(data[1])
local ts = tonumber(data[2])

if tokens == nil then
  tokens = capacity
  ts = now_ms
end

local delta = math.max(0, now_ms - ts)
tokens = math.min(capacity, tokens + (delta * rate))
ts = now_ms

-- Absolute RPM window
redis.call('ZREMRANGEBYSCORE', window_key, 0, window_start)
local count = redis.call('ZCARD', window_key)
if count >= limit then
  local oldest = redis.call('ZRANGE', window_key, 0, 0, 'WITHSCORES')
  local wait_hint = 1
  if oldest and #oldest >= 2 then
    local oldest_ts = tonumber(oldest[2])
    wait_hint = math.max(1, (oldest_ts + window_seconds) - now)
  end
  redis.call("HMSET", bucket_key, "tokens", tokens, "ts", ts)
  redis.call("PEXPIRE", bucket_key, 120000)
  return {-1, wait_hint}
end

if tokens >= 1 then
  tokens = tokens - 1
  redis.call("HMSET", bucket_key, "tokens", tokens, "ts", ts)
  redis.call("PEXPIRE", bucket_key, 120000)
  redis.call('ZADD', window_key, now, request_id)
  redis.call('EXPIRE', window_key, window_seconds + 10)
  return {1, tokens}
else
  local needed = 1 - tokens
  local wait = math.ceil(needed / rate)
  redis.call("HMSET", bucket_key, "tokens", tokens, "ts", ts)
  redis.call("PEXPIRE", bucket_key, 120000)
  return {0, wait}
end
"""

# Lua script for TPM sliding window with running sum (absolute per-minute cap)
# Keys: zset, sum_key, cost_map
# Returns: {1, new_sum} on success, {0, wait_hint} on failure
TPM_SLIDING_WINDOW_SCRIPT = """
local zkey = KEYS[1]
local sum_key = KEYS[2]
local cost_key = KEYS[3]

local limit = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])
local request_id = ARGV[5]
local window_seconds = tonumber(ARGV[6])

local sum = tonumber(redis.call('GET', sum_key) or "0")
local expired = redis.call('ZRANGEBYSCORE', zkey, 0, window_start)
for i = 1, #expired do
  local id = expired[i]
  local t = tonumber(redis.call('HGET', cost_key, id) or "0")
  if t > 0 then
    sum = sum - t
    redis.call('HDEL', cost_key, id)
  end
end
if sum < 0 then
  sum = 0
end
if #expired > 0 then
  redis.call('ZREMRANGEBYSCORE', zkey, 0, window_start)
end

if (sum + cost) <= limit then
  redis.call('ZADD', zkey, now, request_id)
  redis.call('HSET', cost_key, request_id, cost)
  sum = sum + cost
  redis.call('SET', sum_key, sum)
  redis.call('EXPIRE', zkey, window_seconds + 10)
  redis.call('EXPIRE', cost_key, window_seconds + 10)
  redis.call('EXPIRE', sum_key, window_seconds + 10)
  return {1, sum}
end

redis.call('SET', sum_key, sum)
redis.call('EXPIRE', sum_key, window_seconds + 10)

local needed = (sum + cost) - limit
local entries = redis.call('ZRANGE', zkey, 0, -1, 'WITHSCORES')
local wait_hint = 1
for i = 1, #entries, 2 do
  local id = entries[i]
  local score = tonumber(entries[i + 1])
  local t = tonumber(redis.call('HGET', cost_key, id) or "0")
  if t > 0 then
    needed = needed - t
    if needed <= 0 then
      wait_hint = math.max(1, (score + window_seconds) - now)
      break
    end
  end
end

return {0, wait_hint}
"""


class ModelRateLimiter:
    """
    Redis-backed global rate limiter for LLM API calls.

    Keys are global per model. No per-user or per-workflow caps.
    """

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._script = None  # Lazy-loaded Lua script (RPD)
        self._rpm_script = None
        self._tpm_script = None

    async def _get_script(self):
        """Lazily register the RPD Lua script with Redis."""
        if self._script is None:
            self._script = self._redis.register_script(RATE_LIMIT_SCRIPT)
        return self._script

    async def _get_rpm_script(self):
        if self._rpm_script is None:
            self._rpm_script = self._redis.register_script(RPM_COMBINED_SCRIPT)
        return self._rpm_script

    async def _get_tpm_script(self):
        if self._tpm_script is None:
            self._tpm_script = self._redis.register_script(TPM_SLIDING_WINDOW_SCRIPT)
        return self._tpm_script

    def _get_limit(self, model_name: str) -> int:
        """Get RPM limit for a model, falling back to default."""
        return MODEL_RATE_LIMITS.get(model_name, MODEL_RATE_LIMITS["__default__"])

    def _get_tpm_limit(self, model_name: str) -> int:
        return MODEL_TPM_LIMITS.get(model_name, MODEL_TPM_LIMITS["__default__"])

    def _get_rpd_limit(self, model_name: str) -> int:
        return MODEL_RPD_LIMITS.get(model_name, MODEL_RPD_LIMITS["__default__"])

    def _tpm_keys(self, model_name: str) -> tuple[str, str, str]:
        base = f"ratelimit:tpm:global:{model_name}"
        return (f"{base}:zset", f"{base}:sum", f"{base}:costs")

    def _rpm_bucket_key(self, model_name: str) -> str:
        return f"ratelimit:rpm:bucket:{model_name}"

    def _rpm_window_key(self, model_name: str) -> str:
        return f"ratelimit:rpm:window:{model_name}"

    def _rpd_key(self, model_name: str) -> str:
        return f"ratelimit:rpd:global:{model_name}"

    async def acquire(
        self,
        model_name: str,
        timeout: float = 30.0,
    ) -> bool:
        """
        Smooth requests per minute using a token bucket.
        
        Args:
            model_name: Full model name (e.g., "openrouter/google/gemini-3-flash-preview")
            timeout: Max seconds to wait before raising RuntimeError
            
        Returns:
            True if acquired successfully
            
        Raises:
            RuntimeError: If timeout exceeded waiting for rate limit
        """
        limit = self._get_limit(model_name)
        bucket_key = self._rpm_bucket_key(model_name)
        window_key = self._rpm_window_key(model_name)
        capacity = max(1, int((limit / 60.0) * RPM_BURST_SECONDS))
        rate_per_ms = limit / 60000.0
        window_seconds = 60

        deadline = time.monotonic() + timeout
        attempt = 0

        try:
            script = await self._get_rpm_script()
        except redis.RedisError as e:
            logger.warning("Redis error registering rate limit script: %s", e)
            return True  # Fail open

        while time.monotonic() < deadline:
            try:
                now_ms = int(time.time() * 1000)
                now = int(time.time())
                window_start = now - window_seconds
                request_id = f"{now}:{id(asyncio.current_task())}:{attempt}"

                result = await script(
                    keys=[bucket_key, window_key],
                    args=[capacity, rate_per_ms, now_ms, limit, window_start, now, request_id, window_seconds],
                )

                if result[0] == 1:
                    return True

                if result[0] == -1:
                    wait_hint = result[1]
                    wait_time = min(max(0.5, wait_hint), 2.0)
                    logger.info(
                        "RPM limit hit for %s (limit=%d), waiting %.1fs",
                        model_name, limit, wait_time
                    )
                    await asyncio.sleep(wait_time)
                    attempt += 1
                    continue

                wait_ms = int(result[1])
                wait_ms = min(max(10, wait_ms), 500)
                if wait_ms > 200:
                    logger.info(
                        "RPM smoothing wait for %s (limit=%d), waiting %dms",
                        model_name, limit, wait_ms
                    )
                await asyncio.sleep((wait_ms + random.randint(0, 50)) / 1000.0)
                attempt += 1

            except redis.RedisError as e:
                logger.warning("Redis error in rate limiter: %s", e)
                # On Redis failure, allow the request (fail open)
                return True

        raise RuntimeError(
            f"Rate limit timeout for model {model_name} after {timeout}s "
            f"(limit: {limit} req/min)"
        )

    async def acquire_rpd(
        self,
        model_name: str,
        timeout: float = 30.0,
    ) -> bool:
        limit = self._get_rpd_limit(model_name)
        key = self._rpd_key(model_name)
        window_seconds = 86400

        deadline = time.monotonic() + timeout
        attempt = 0

        try:
            script = await self._get_script()
        except redis.RedisError as e:
            logger.warning("Redis error registering RPD script: %s", e)
            return True

        while time.monotonic() < deadline:
            now = int(time.time())
            window_start = now - window_seconds
            request_id = f"{now}:{id(asyncio.current_task())}:{attempt}"

            try:
                result = await script(
                    keys=[key],
                    args=[limit, window_start, now, request_id, window_seconds],
                )
                success = result[0]
                if success == 1:
                    return True

                wait_hint = result[1]
                wait_time = min(max(1.0, wait_hint), 5.0)
                logger.info(
                    "RPD limit hit for %s (limit=%d), waiting %.1fs",
                    model_name, limit, wait_time
                )
                await asyncio.sleep(wait_time)
                attempt += 1
            except redis.RedisError as e:
                logger.warning("Redis error in RPD limiter: %s", e)
                return True

        raise RuntimeError(
            f"RPD rate limit timeout for model {model_name} after {timeout}s "
            f"(limit: {limit} req/day)"
        )

    async def acquire_tpm(
        self,
        model_name: str,
        tokens: int,
        *,
        timeout: float = 30.0,
    ) -> bool:
        if tokens <= 0:
            return True

        tpm_limit = self._get_tpm_limit(model_name)
        zkey, sum_key, cost_key = self._tpm_keys(model_name)
        window_ms = 60000

        deadline = time.monotonic() + timeout
        attempt = 0

        try:
            script = await self._get_tpm_script()
        except redis.RedisError as e:
            logger.warning("Redis error registering TPM script: %s", e)
            return True

        while time.monotonic() < deadline:
            now_ms = int(time.time() * 1000)
            window_start = now_ms - window_ms
            request_id = f"{now_ms}:{id(asyncio.current_task())}:{attempt}"
            try:
                result = await script(
                    keys=[zkey, sum_key, cost_key],
                    args=[tpm_limit, window_start, now_ms, tokens, request_id, window_ms],
                )
                success = result[0]
                if success == 1:
                    return True

                wait_hint = result[1]
                wait_time = min(max(0.5, wait_hint / 1000.0), 2.0)
                logger.info(
                    "TPM limit hit for %s (limit=%d), waiting %.1fs",
                    model_name, tpm_limit, wait_time
                )
                await asyncio.sleep(wait_time)
                attempt += 1

            except redis.RedisError as e:
                logger.warning("Redis error in TPM limiter: %s", e)
                return True

        raise RuntimeError(
            f"TPM rate limit timeout for model {model_name} after {timeout}s "
            f"(limit: {tpm_limit} tokens/min)"
        )


# Singleton instance - initialized lazily with Redis client
_limiter_instance: Optional[ModelRateLimiter] = None


def get_rate_limiter(redis_client: redis.Redis) -> ModelRateLimiter:
    """Get or create the global rate limiter instance."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = ModelRateLimiter(redis_client)
    return _limiter_instance
