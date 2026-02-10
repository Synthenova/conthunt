"""Database session and engine management."""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event, text
from sqlalchemy.pool import NullPool

from app.core import get_settings, logger
from app.db.db_semaphore import db_slot, get_db_kind, get_global_db_semaphore

settings = get_settings()

connect_args = {}
poolclass = None

def _looks_like_pgbouncer(url: str) -> bool:
    try:
        # SQLAlchemy URLs: postgresql+asyncpg://...
        u = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        parsed = urlparse(u)
        if parsed.hostname in {"pgbouncer"}:
            return True
        if parsed.port == 6432:
            return True
    except Exception:
        pass
    return False


if settings.DB_PGBOUNCER_MODE.lower() == "transaction" or _looks_like_pgbouncer(settings.DATABASE_URL):
    # asyncpg caches prepared statements; that can break behind transaction poolers.
    connect_args["statement_cache_size"] = 0
    # Keep app-side pool small; PgBouncer is the pool.
    # (Leave pool sizing configurable; see settings.DB_POOL_SIZE/OVERFLOW.)

# Optional: disable SQLAlchemy pooling and let PgBouncer handle pooling/multiplexing.
# This prevents app-side QueuePool timeouts when concurrency spikes (e.g. deep research fanout).
if bool(getattr(settings, "DB_USE_NULLPOOL", False)):
    poolclass = NullPool

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    **(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
        }
        if poolclass is None
        else {}
    ),
    poolclass=poolclass,
    connect_args=connect_args,
)


@event.listens_for(engine.sync_engine, "connect")
def set_search_path(dbapi_conn, connection_record):
    """Set search_path on every new connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")
    cursor.close()


# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""
    sem = get_global_db_semaphore()
    kind = get_db_kind()
    max_wait_ms = settings.DB_SEM_TASKS_MAX_WAIT_MS if kind == "tasks" else settings.DB_SEM_API_MAX_WAIT_MS
    fail_status = 503 if kind == "tasks" else 429

    if settings.DB_SEMAPHORE_ENABLED and sem is not None:
        try:
            async with db_slot(sem, kind, max_wait_ms=max_wait_ms, fail_status=fail_status):
                async with async_session_factory() as session:
                    try:
                        yield session
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
                return
        except Exception as exc:
            # Fail-open only for Redis/semaphore errors; busy is an HTTPException and should propagate.
            from fastapi import HTTPException
            if isinstance(exc, HTTPException):
                raise
            logger.warning("DB semaphore error in get_db_session (fail-open): %s", exc, exc_info=True)

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Get raw async connection for RLS operations."""
    sem = get_global_db_semaphore()
    kind = get_db_kind()
    max_wait_ms = settings.DB_SEM_TASKS_MAX_WAIT_MS if kind == "tasks" else settings.DB_SEM_API_MAX_WAIT_MS
    fail_status = 503 if kind == "tasks" else 429

    if settings.DB_SEMAPHORE_ENABLED and sem is not None:
        try:
            async with db_slot(sem, kind, max_wait_ms=max_wait_ms, fail_status=fail_status):
                async with engine.connect() as conn:
                    await conn.execute(text(f"SET search_path TO {settings.DB_SCHEMA}, public"))
                    try:
                        yield conn
                        await conn.commit()
                    except Exception:
                        await conn.rollback()
                        raise
                return
        except Exception as exc:
            from fastapi import HTTPException
            if isinstance(exc, HTTPException):
                raise
            logger.warning("DB semaphore error in get_db_connection (fail-open): %s", exc, exc_info=True)

    async with engine.connect() as conn:
        await conn.execute(text(f"SET search_path TO {settings.DB_SCHEMA}, public"))
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


async def init_db() -> None:
    """Initialize database (verify connection)."""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    """Close database engine."""
    await engine.dispose()
