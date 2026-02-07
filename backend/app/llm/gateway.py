from __future__ import annotations

import asyncio
import hashlib
import math
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Optional

import httpx

from app.core import logger, get_settings
from app.llm.context import get_llm_route, get_llm_user_id
from app.llm.limits import get_model_limits


@dataclass
class LLMJob:
    job_id: str
    model_name: str
    user_id: str
    route: str
    estimated_tokens: int
    attempts: int


class PermitTimeoutError(RuntimeError):
    pass


class LLMGateway:
    def __init__(
        self,
        redis_client,
        instance_id: str | None = None,
        *,
        default_est_tokens: int = 12000,
        stats_window: int = 200,
        scheduler_poll_ms: int = 50,
        lock_ttl_ms: int = 15000,
        permit_ttl_ms: int = 300000,
        jitter_max_ms: int = 100,
        backoff_base_s: float = 1.0,
        backoff_cap_s: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        self.redis = redis_client
        self.instance_id = instance_id or str(uuid.uuid4())
        self.default_est_tokens = default_est_tokens
        self.stats_window = stats_window
        self.scheduler_poll_ms = scheduler_poll_ms
        self.lock_ttl_ms = lock_ttl_ms
        self.permit_ttl_ms = permit_ttl_ms
        self.jitter_max_ms = jitter_max_ms
        self.backoff_base_s = backoff_base_s
        self.backoff_cap_s = backoff_cap_s
        self.max_retries = max_retries
        self._jobs: dict[str, LLMJob] = {}
        self._scheduler_tasks: dict[str, asyncio.Task] = {}
        self._stats_cache: dict[str, dict[str, float]] = {}
        self._debug = get_settings().LLM_GATEWAY_DEBUG

    def _log_debug(self, msg: str, *args: Any) -> None:
        if self._debug:
            logger.info(msg, *args)

    async def run_invoke(
        self,
        model_name: str,
        user_id: str | None,
        route: str | None,
        call_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        job = await self._prepare_job(model_name, user_id, route)
        try:
            return await self._execute_with_retries(job, call_fn, *args, **kwargs)
        finally:
            self._jobs.pop(job.job_id, None)

    async def run_stream(
        self,
        model_name: str,
        user_id: str | None,
        route: str | None,
        call_fn: Callable[..., AsyncIterator[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[Any]:
        job = await self._prepare_job(model_name, user_id, route)

        async def _gen() -> AsyncIterator[Any]:
            try:
                async for chunk in self._execute_stream(job, call_fn, *args, **kwargs):
                    yield chunk
            finally:
                self._jobs.pop(job.job_id, None)

        return _gen()

    async def _prepare_job(
        self,
        model_name: str,
        user_id: str | None,
        route: str | None,
    ) -> LLMJob:
        resolved_user_id = user_id or get_llm_user_id() or "system:unknown"
        resolved_route = route or get_llm_route() or "default"
        estimated_tokens = await self._estimate_tokens(model_name, resolved_route)
        job_id = str(uuid.uuid4())
        job = LLMJob(
            job_id=job_id,
            model_name=model_name,
            user_id=resolved_user_id,
            route=resolved_route,
            estimated_tokens=estimated_tokens,
            attempts=0,
        )
        self._jobs[job_id] = job
        self._ensure_scheduler(job.model_name)
        self._log_debug(
            "[LLM] Enqueued job=%s model=%s user=%s route=%s est_tokens=%s attempt=%s",
            job.job_id,
            job.model_name,
            job.user_id,
            job.route,
            job.estimated_tokens,
            job.attempts,
        )
        return job

    async def _enqueue_job(self, job: LLMJob) -> None:
        queue_key = f"llm:queue:{job.model_name}:{job.user_id}"
        active_key = f"llm:active_users:{job.model_name}"
        job_key = f"llm:job:{job.job_id}"
        enqueued_key = f"llm:enqueued:{job.job_id}:{job.attempts}"
        payload = {
            "job_id": job.job_id,
            "model": job.model_name,
            "user_id": job.user_id,
            "route": job.route,
            "estimated_tokens": str(job.estimated_tokens),
            "attempts": str(job.attempts),
            "owner": self.instance_id,
            "enqueued_at_ms": str(int(time.time() * 1000)),
        }
        pipe = self.redis.pipeline()
        pipe.set(enqueued_key, "1", nx=True, ex=3600)
        pipe.hset(job_key, mapping=payload)
        pipe.expire(job_key, 3600)
        results = await pipe.execute()
        if not results or not results[0]:
            return
        pipe = self.redis.pipeline()
        pipe.rpush(queue_key, job.job_id)
        pipe.zadd(active_key, {job.user_id: 0})
        await pipe.execute()

    def _ensure_scheduler(self, model_name: str) -> None:
        if model_name in self._scheduler_tasks:
            return
        task = asyncio.create_task(self._scheduler_loop(model_name))
        self._scheduler_tasks[model_name] = task

    async def _scheduler_loop(self, model_name: str) -> None:
        lock_key = f"llm:scheduler:lock:{model_name}"
        lock_value = f"{self.instance_id}:{uuid.uuid4()}"
        next_renew_at = 0.0

        while True:
            now = time.time()
            if now >= next_renew_at:
                acquired = await self._try_acquire_or_renew_lock(lock_key, lock_value)
                if not acquired:
                    await asyncio.sleep(1.0)
                    continue
                next_renew_at = now + (self.lock_ttl_ms / 1000) * 0.6

            try:
                current = await self.redis.get(lock_key)
                if current != lock_value:
                    next_renew_at = 0.0
                    await asyncio.sleep(0.2)
                    continue
                await self._schedule_once(model_name)
            except Exception as exc:
                logger.warning("LLM scheduler error for %s: %s", model_name, exc)
                await asyncio.sleep(0.2)

    async def _try_acquire_or_renew_lock(self, lock_key: str, lock_value: str) -> bool:
        # Attempt to acquire
        acquired = await self.redis.set(lock_key, lock_value, nx=True, px=self.lock_ttl_ms)
        if acquired:
            return True
        # Attempt to renew if we already own it
        lua = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("PEXPIRE", KEYS[1], ARGV[2])
        end
        return 0
        """
        res = await self.redis.eval(lua, 1, lock_key, lock_value, self.lock_ttl_ms)
        return bool(res)

    async def _schedule_once(self, model_name: str) -> None:
        limits = get_model_limits(model_name)
        now_ms = int(time.time() * 1000)

        await self._evict_expired_active_jobs(model_name, now_ms)

        # Concurrency check (global)
        target_in_flight = await self._get_target_in_flight(model_name)
        in_flight = await self.redis.zcard(f"llm:active_jobs:{model_name}")
        if in_flight >= target_in_flight:
            await asyncio.sleep(self.scheduler_poll_ms / 1000)
            return

        user_id, job_id = await self._pop_next_job(model_name)
        if not job_id:
            await asyncio.sleep(self.scheduler_poll_ms / 1000)
            return

        job_key = f"llm:job:{job_id}"
        job_data = await self.redis.hgetall(job_key)
        if not job_data:
            return
        scheduled_key = f"llm:scheduled:{job_id}"
        scheduled = await self.redis.set(scheduled_key, self.instance_id, nx=True, px=self.permit_ttl_ms)
        if not scheduled:
            return

        est_tokens = int(job_data.get("estimated_tokens") or self.default_est_tokens)
        rpm_interval_ms = max(1, int(60000 / max(limits.rpm, 1)))
        tpm_tokens_per_ms = max(limits.tpm / 60000.0, 1e-6)
        tpm_interval_ms = max(1, int(est_tokens / tpm_tokens_per_ms))

        rpd_start_at = await self._reserve_rpd_slot(model_name, limits.rpd, now_ms)

        start_at = await self._reserve_start_time(
            model_name,
            now_ms,
            rpm_interval_ms,
            tpm_interval_ms,
            rpd_start_at,
        )

        permit_key = f"llm:permit:{job_id}"
        await self.redis.set(permit_key, str(start_at), px=self.permit_ttl_ms)
        self._log_debug(
            "[LLM] Permit job=%s model=%s user=%s start_at=%s rpm_ms=%s tpm_ms=%s rpd_at=%s est_tokens=%s",
            job_id,
            model_name,
            user_id,
            start_at,
            rpm_interval_ms,
            tpm_interval_ms,
            rpd_start_at,
            est_tokens,
        )

    async def _pop_next_job(self, model_name: str) -> tuple[Optional[str], Optional[str]]:
        lua = """
        local active_key = KEYS[1]
        local cursor_key = KEYS[2]
        local queue_prefix = ARGV[1]
        local cursor = redis.call("GET", cursor_key)
        local next_user = nil
        if cursor then
            local res = redis.call("ZRANGEBYLEX", active_key, "(" .. cursor, "+", "LIMIT", 0, 1)
            if #res > 0 then
                next_user = res[1]
            end
        end
        if not next_user then
            local res = redis.call("ZRANGEBYLEX", active_key, "-", "+", "LIMIT", 0, 1)
            if #res > 0 then
                next_user = res[1]
            end
        end
        if not next_user then
            return {false, false}
        end
        local job_id = redis.call("LPOP", queue_prefix .. next_user)
        if not job_id then
            redis.call("ZREM", active_key, next_user)
            return {next_user, false}
        end
        local remaining = redis.call("LLEN", queue_prefix .. next_user)
        if remaining == 0 then
            redis.call("ZREM", active_key, next_user)
        end
        redis.call("SET", cursor_key, next_user)
        return {next_user, job_id}
        """
        active_key = f"llm:active_users:{model_name}"
        cursor_key = f"llm:rr_cursor:{model_name}"
        queue_prefix = f"llm:queue:{model_name}:"
        res = await self.redis.eval(lua, 2, active_key, cursor_key, queue_prefix)
        if not res or len(res) < 2:
            return None, None
        user_id = res[0] if res[0] else None
        job_id = res[1] if res[1] else None
        return user_id, job_id

    async def _reserve_start_time(
        self,
        model_name: str,
        now_ms: int,
        rpm_interval_ms: int,
        tpm_interval_ms: int,
        rpd_start_at: int,
    ) -> int:
        lua = """
        local now = tonumber(ARGV[1])
        local rpm_interval = tonumber(ARGV[2])
        local tpm_interval = tonumber(ARGV[3])
        local rpd_start = tonumber(ARGV[4])
        local next_rpm = tonumber(redis.call("GET", KEYS[1]) or 0)
        local next_tpm = tonumber(redis.call("GET", KEYS[2]) or 0)
        local start_at = math.max(now, next_rpm, next_tpm, rpd_start)
        redis.call("SET", KEYS[1], start_at + rpm_interval)
        redis.call("SET", KEYS[2], start_at + tpm_interval)
        return start_at
        """
        key_rpm = f"llm:next_start_rpm_ms:{model_name}"
        key_tpm = f"llm:next_start_tpm_ms:{model_name}"
        start_at = await self.redis.eval(
            lua,
            2,
            key_rpm,
            key_tpm,
            now_ms,
            rpm_interval_ms,
            tpm_interval_ms,
            rpd_start_at,
        )
        return int(start_at)

    async def _reserve_rpd_slot(self, model_name: str, rpd_limit: int, now_ms: int) -> int:
        key = f"llm:rpd:{model_name}"
        window_start = now_ms - 86400000
        lua = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local member = ARGV[4]
        redis.call("ZREMRANGEBYSCORE", key, 0, window_start)
        local count = redis.call("ZCARD", key)
        if count < limit then
            redis.call("ZADD", key, now, member)
            return now
        end
        local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
        if #oldest >= 2 then
            local oldest_ms = tonumber(oldest[2])
            local start_at = math.max(now, oldest_ms + 86400000)
            redis.call("ZADD", key, start_at, member)
            return start_at
        end
        redis.call("ZADD", key, now, member)
        return now
        """
        start_at = await self.redis.eval(
            lua,
            1,
            key,
            now_ms,
            window_start,
            rpd_limit,
            str(uuid.uuid4()),
        )
        return int(start_at)

    async def _await_permit(self, job: LLMJob) -> int:
        permit_key = f"llm:permit:{job.job_id}"
        start = time.monotonic()
        max_wait_s = 60.0
        while True:
            raw = await self.redis.get(permit_key)
            if raw:
                return int(raw)
            if time.monotonic() - start > max_wait_s:
                self._log_debug("[LLM] Permit timeout job=%s", job.job_id)
                raise PermitTimeoutError(f"Timed out waiting for permit {job.job_id}")
            await asyncio.sleep(self.scheduler_poll_ms / 1000)

    async def _acquire_in_flight(self, model_name: str, job_id: str) -> None:
        active_key = f"llm:active_jobs:{model_name}"
        while True:
            now_ms = int(time.time() * 1000)
            target = await self._get_target_in_flight(model_name)
            p95_ms, _ = await self._get_latency_p95_ms(model_name)
            expires_at = now_ms + max(int(p95_ms * 2), 120000)
            lua = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local target = tonumber(ARGV[2])
            local job_id = ARGV[3]
            local expires_at = tonumber(ARGV[4])
            redis.call("ZREMRANGEBYSCORE", key, 0, now)
            local count = redis.call("ZCARD", key)
            if count < target then
                redis.call("ZADD", key, expires_at, job_id)
                return 1
            end
            return 0
            """
            acquired = await self.redis.eval(lua, 1, active_key, now_ms, target, job_id, expires_at)
            if acquired == 1 or acquired is True:
                self._log_debug(
                    "[LLM] In-flight acquired job=%s model=%s target=%s expires_at=%s",
                    job_id,
                    model_name,
                    target,
                    expires_at,
                )
                return
            await asyncio.sleep(0.05)

    async def _evict_expired_active_jobs(self, model_name: str, now_ms: int) -> None:
        active_key = f"llm:active_jobs:{model_name}"
        await self.redis.zremrangebyscore(active_key, 0, now_ms)

    async def _execute_with_retries(
        self,
        job: LLMJob,
        call_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        while True:
            job.attempts += 1
            await self._enqueue_job(job)
            start_at = await self._await_permit(job)
            await self._sleep_until(start_at, job.user_id, job.job_id)
            await self._acquire_in_flight(job.model_name, job.job_id)

            start_time = time.monotonic()
            try:
                result = await call_fn(*args, **kwargs)
                latency_ms = int((time.monotonic() - start_time) * 1000)
                await self._record_success(job, result, latency_ms)
                self._log_debug(
                    "[LLM] Success job=%s model=%s latency_ms=%s",
                    job.job_id,
                    job.model_name,
                    latency_ms,
                )
                return result
            except asyncio.CancelledError:
                await self._finalize_active(job)
                raise
            except PermitTimeoutError as exc:
                await self._finalize_active(job)
                if job.attempts >= self.max_retries:
                    raise
                delay = self._compute_backoff_delay(job.attempts, exc)
                self._log_debug(
                    "[LLM] Permit retry job=%s model=%s attempt=%s delay=%.2fs",
                    job.job_id,
                    job.model_name,
                    job.attempts,
                    delay,
                )
                await asyncio.sleep(delay)
            except Exception as exc:
                await self._finalize_active(job)
                if not self._is_retryable(exc) or job.attempts >= self.max_retries:
                    raise
                delay = self._compute_backoff_delay(job.attempts, exc)
                self._log_debug(
                    "[LLM] Retry job=%s model=%s attempt=%s delay=%.2fs err=%s",
                    job.job_id,
                    job.model_name,
                    job.attempts,
                    delay,
                    type(exc).__name__,
                )
                await asyncio.sleep(delay)

    async def _execute_stream(
        self,
        job: LLMJob,
        call_fn: Callable[..., AsyncIterator[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[Any]:
        while True:
            job.attempts += 1
            await self._enqueue_job(job)
            start_at = await self._await_permit(job)
            await self._sleep_until(start_at, job.user_id, job.job_id)
            await self._acquire_in_flight(job.model_name, job.job_id)

            start_time = time.monotonic()
            streamed_any = False
            last_usage_obj: Any = None
            try:
                async for chunk in call_fn(*args, **kwargs):
                    streamed_any = True
                    if self._extract_tokens(chunk):
                        last_usage_obj = chunk
                    yield chunk
                latency_ms = int((time.monotonic() - start_time) * 1000)
                await self._record_success(job, last_usage_obj, latency_ms)
                self._log_debug(
                    "[LLM] Stream success job=%s model=%s latency_ms=%s",
                    job.job_id,
                    job.model_name,
                    latency_ms,
                )
                return
            except asyncio.CancelledError:
                await self._finalize_active(job)
                raise
            except PermitTimeoutError as exc:
                await self._finalize_active(job)
                if job.attempts >= self.max_retries:
                    raise
                delay = self._compute_backoff_delay(job.attempts, exc)
                self._log_debug(
                    "[LLM] Stream permit retry job=%s model=%s attempt=%s delay=%.2fs",
                    job.job_id,
                    job.model_name,
                    job.attempts,
                    delay,
                )
                await asyncio.sleep(delay)
            except Exception as exc:
                await self._finalize_active(job)
                if streamed_any:
                    raise
                if not self._is_retryable(exc) or job.attempts >= self.max_retries:
                    raise
                delay = self._compute_backoff_delay(job.attempts, exc)
                self._log_debug(
                    "[LLM] Stream retry job=%s model=%s attempt=%s delay=%.2fs err=%s",
                    job.job_id,
                    job.model_name,
                    job.attempts,
                    delay,
                    type(exc).__name__,
                )
                await asyncio.sleep(delay)

    async def _record_success(self, job: LLMJob, result: Any, latency_ms: int) -> None:
        await self._finalize_active(job)
        tokens = self._extract_tokens(result) or job.estimated_tokens
        await self._reconcile_tpm(job.model_name, job.estimated_tokens, tokens)
        await self._record_stats(job.model_name, job.route, tokens, latency_ms)
        self._log_debug(
            "[LLM] Stats job=%s model=%s route=%s tokens=%s latency_ms=%s",
            job.job_id,
            job.model_name,
            job.route,
            tokens,
            latency_ms,
        )

    async def _finalize_active(self, job: LLMJob) -> None:
        active_key = f"llm:active_jobs:{job.model_name}"
        permit_key = f"llm:permit:{job.job_id}"
        job_key = f"llm:job:{job.job_id}"
        scheduled_key = f"llm:scheduled:{job.job_id}"
        pipe = self.redis.pipeline()
        pipe.zrem(active_key, job.job_id)
        pipe.delete(permit_key)
        pipe.delete(job_key)
        pipe.delete(scheduled_key)
        await pipe.execute()

    async def _record_stats(self, model_name: str, route: str, tokens: int, latency_ms: int) -> None:
        lat_key = f"llm:stats:{model_name}:latency_ms"
        tok_key = f"llm:stats:{model_name}:tokens"
        route_key = f"llm:stats:{model_name}:route:{route}:tokens"
        pipe = self.redis.pipeline()
        pipe.lpush(lat_key, latency_ms)
        pipe.ltrim(lat_key, 0, self.stats_window - 1)
        pipe.lpush(tok_key, tokens)
        pipe.ltrim(tok_key, 0, self.stats_window - 1)
        pipe.lpush(route_key, tokens)
        pipe.ltrim(route_key, 0, self.stats_window - 1)
        await pipe.execute()
        self._stats_cache.pop(model_name, None)

    async def _reconcile_tpm(self, model_name: str, reserved_tokens: int, actual_tokens: int) -> None:
        delta = actual_tokens - reserved_tokens
        if delta == 0:
            return
        limits = get_model_limits(model_name)
        tpm_tokens_per_ms = max(limits.tpm / 60000.0, 1e-6)
        delta_ms = int(delta / tpm_tokens_per_ms)
        lua = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local delta = tonumber(ARGV[2])
        local next = tonumber(redis.call("GET", key) or 0)
        next = math.max(now, next + delta)
        redis.call("SET", key, next)
        return next
        """
        key_tpm = f"llm:next_start_tpm_ms:{model_name}"
        await self.redis.eval(lua, 1, key_tpm, int(time.time() * 1000), delta_ms)
        self._log_debug(
            "[LLM] TPM reconcile model=%s reserved=%s actual=%s delta_ms=%s",
            model_name,
            reserved_tokens,
            actual_tokens,
            delta_ms,
        )

    async def _estimate_tokens(self, model_name: str, route: str) -> int:
        route_key = f"llm:stats:{model_name}:route:{route}:tokens"
        values = await self.redis.lrange(route_key, 0, self.stats_window - 1)
        if len(values) >= 5:
            avg = sum(int(v) for v in values) / len(values)
            return max(1, int(avg * 1.1))
        avg_tokens, _ = await self._get_avg_tokens(model_name)
        if avg_tokens:
            return max(1, int(avg_tokens * 1.1))
        return self.default_est_tokens

    async def _get_avg_tokens(self, model_name: str) -> tuple[Optional[float], int]:
        cache = self._stats_cache.get(model_name)
        now = time.time()
        if cache and now - cache.get("ts", 0) < 5 and "avg_tokens" in cache:
            return cache["avg_tokens"], 0

        tok_key = f"llm:stats:{model_name}:tokens"
        values = await self.redis.lrange(tok_key, 0, self.stats_window - 1)
        if not values:
            self._stats_cache[model_name] = {"avg_tokens": 0.0, "ts": now}
            return None, 0
        ints = [int(v) for v in values]
        avg = sum(ints) / len(ints)
        cache = cache or {}
        cache.update({"avg_tokens": avg, "ts": now})
        self._stats_cache[model_name] = cache
        return avg, 0

    async def _get_latency_p95_ms(self, model_name: str) -> tuple[int, int]:
        cache = self._stats_cache.get(model_name)
        now = time.time()
        if cache and now - cache.get("ts", 0) < 5 and "p95_latency_ms" in cache:
            return int(cache["p95_latency_ms"]), int(cache.get("ts", now))

        lat_key = f"llm:stats:{model_name}:latency_ms"
        values = await self.redis.lrange(lat_key, 0, self.stats_window - 1)
        if not values:
            self._stats_cache[model_name] = {"p95_latency_ms": 60000.0, "ts": now}
            return 60000, int(now)
        ints = [int(v) for v in values]
        p95 = self._percentile(ints, 95)
        cache = cache or {}
        cache.update({"p95_latency_ms": float(p95), "ts": now})
        self._stats_cache[model_name] = cache
        return int(p95), int(now)

    async def _get_target_in_flight(self, model_name: str) -> int:
        limits = get_model_limits(model_name)
        avg_tokens, _ = await self._get_avg_tokens(model_name)
        if not avg_tokens:
            avg_tokens = self.default_est_tokens
        p95_ms, _ = await self._get_latency_p95_ms(model_name)
        starts_per_sec = (limits.tpm / 60) / max(avg_tokens, 1)
        target = math.ceil(starts_per_sec * (p95_ms / 1000) * 1.3)
        return max(1, min(target, 1000))

    def _extract_tokens(self, result: Any) -> Optional[int]:
        if result is None:
            return None
        usage = getattr(result, "usage_metadata", None)
        if isinstance(usage, dict):
            total = usage.get("total_tokens") or usage.get("totalTokenCount")
            if total:
                return int(total)
        meta = getattr(result, "response_metadata", None)
        if isinstance(meta, dict):
            for key in ("token_usage", "usage", "usage_metadata"):
                payload = meta.get(key)
                if isinstance(payload, dict):
                    total = payload.get("total_tokens") or payload.get("totalTokenCount")
                    if total:
                        return int(total)
        return None

    def _is_retryable(self, exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in (429, 500, 503, 504)
        status = getattr(exc, "status_code", None)
        if status in (429, 500, 503, 504):
            return True
        return False

    def _compute_backoff_delay(self, attempt: int, exc: Exception) -> float:
        provider_delay = self._extract_retry_after(exc)
        delay = min(self.backoff_cap_s, self.backoff_base_s * (2 ** attempt))
        delay = max(delay, provider_delay or 0)
        return random.random() * delay

    def _extract_retry_after(self, exc: Exception) -> Optional[float]:
        if isinstance(exc, httpx.HTTPStatusError):
            header = exc.response.headers.get("retry-after")
            if header:
                try:
                    return float(header)
                except ValueError:
                    return None
        retry_delay = getattr(exc, "retry_delay", None)
        if retry_delay:
            try:
                return float(retry_delay)
            except Exception:
                return None
        return None

    async def _sleep_until(self, start_at_ms: int, user_id: str, job_id: str) -> None:
        now_ms = int(time.time() * 1000)
        jitter = self._stable_jitter_ms(user_id, job_id)
        wait_ms = max(0, start_at_ms - now_ms + jitter)
        if wait_ms:
            await asyncio.sleep(wait_ms / 1000)

    def _stable_jitter_ms(self, user_id: str, job_id: str) -> int:
        seed = f"{user_id}:{job_id}".encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()
        val = int(digest[:8], 16)
        return val % max(self.jitter_max_ms, 1)

    @staticmethod
    def _percentile(values: list[int], pct: int) -> int:
        if not values:
            return 0
        values = sorted(values)
        k = (len(values) - 1) * (pct / 100)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return values[int(k)]
        d0 = values[int(f)] * (c - k)
        d1 = values[int(c)] * (k - f)
        return int(d0 + d1)


_gateway: LLMGateway | None = None


def init_gateway(redis_client) -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway(redis_client)
    return _gateway


def get_gateway() -> LLMGateway:
    if _gateway is None:
        raise RuntimeError("LLM gateway is not initialized")
    return _gateway
