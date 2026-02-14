from __future__ import annotations

import asyncio
import contextlib
import contextvars
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass

import redis.asyncio as redis
from fastapi import HTTPException


# Use Redis TIME to avoid clock skew across app instances.
ACQUIRE_LUA = r"""
-- KEYS[1] = sem key
-- ARGV[1] = ttl_ms
-- ARGV[2] = limit
-- ARGV[3] = token

local key = KEYS[1]
local ttl = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local token = ARGV[3]

local t = redis.call("TIME")
local now = (tonumber(t[1]) * 1000) + math.floor(tonumber(t[2]) / 1000)

-- drop expired leases
redis.call("ZREMRANGEBYSCORE", key, "-inf", now)

local count = redis.call("ZCARD", key)
if count >= limit then
  return 0
end

local exp = now + ttl
redis.call("ZADD", key, exp, token)
redis.call("PEXPIRE", key, ttl * 2)
return 1
"""

RELEASE_LUA = r"""
-- KEYS[1] = sem key
-- ARGV[1] = token
return redis.call("ZREM", KEYS[1], ARGV[1])
"""


_db_kind_var: contextvars.ContextVar[str] = contextvars.ContextVar("db_kind", default="api")


@contextlib.contextmanager
def db_kind_override(kind: str):
    tok = _db_kind_var.set(kind)
    try:
        yield
    finally:
        _db_kind_var.reset(tok)


def get_db_kind() -> str:
    return _db_kind_var.get()


@dataclass(frozen=True)
class SemaphoreConfig:
    app_env: str
    key_prefix: str = "sem:db"
    ttl_ms: int = 10_000
    api_limit: int = 7
    tasks_limit: int = 13

    def key_for(self, kind: str) -> str:
        if kind not in ("api", "tasks"):
            kind = "api"
        return f"{self.key_prefix}:{self.app_env}:{kind}"

    def limit_for(self, kind: str) -> int:
        if kind == "tasks":
            return self.tasks_limit
        return self.api_limit


class DBSemaphore:
    def __init__(self, r: redis.Redis, cfg: SemaphoreConfig):
        self.r = r
        self.cfg = cfg
        self._acquire_sha: str | None = None
        self._release_sha: str | None = None

    async def init(self) -> None:
        # Load scripts once for EVALSHA.
        self._acquire_sha = await self.r.script_load(ACQUIRE_LUA)
        self._release_sha = await self.r.script_load(RELEASE_LUA)

    async def acquire(self, kind: str, token: str) -> bool:
        if not self._acquire_sha:
            raise RuntimeError("DBSemaphore not initialized (missing acquire sha)")
        key = self.cfg.key_for(kind)
        limit = self.cfg.limit_for(kind)
        res = await self.r.evalsha(self._acquire_sha, 1, key, self.cfg.ttl_ms, limit, token)
        return bool(res)

    async def release(self, kind: str, token: str) -> None:
        if not self._release_sha:
            raise RuntimeError("DBSemaphore not initialized (missing release sha)")
        key = self.cfg.key_for(kind)
        await self.r.evalsha(self._release_sha, 1, key, token)


_global_sem: DBSemaphore | None = None


def set_global_db_semaphore(sem: DBSemaphore | None) -> None:
    global _global_sem
    _global_sem = sem


def get_global_db_semaphore() -> DBSemaphore | None:
    return _global_sem


@asynccontextmanager
async def db_slot(
    sem: DBSemaphore,
    kind: str,
    *,
    max_wait_ms: int,
    fail_status: int,
    detail: str = "DB busy, retry",
):
    token = str(uuid.uuid4())
    start = time.monotonic()
    sleep_s = 0.03

    while True:
        ok = await sem.acquire(kind, token)
        if ok:
            break

        elapsed_ms = int((time.monotonic() - start) * 1000)
        if elapsed_ms >= max_wait_ms:
            raise HTTPException(status_code=fail_status, detail=detail)

        # bounded retry; small jitter keeps stampedes from syncing
        await asyncio.sleep(sleep_s + (0.01 * (uuid.uuid4().int % 3)))

    try:
        yield
    finally:
        # best-effort release; TTL will self-heal if this fails
        try:
            await sem.release(kind, token)
        except Exception:
            pass

