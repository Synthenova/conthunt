"""Database session and engine management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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

settings = get_settings()

connect_args = {}
poolclass = None


def _normalize_asyncpg_url(url: str) -> tuple[str, dict]:
    # SQLAlchemy's asyncpg dialect passes query params through to asyncpg.connect().
    # Strip libpq-only options like sslmode/channel_binding, and normalize any
    # driverless PostgreSQL URL to the asyncpg dialect explicitly.
    normalized_connect_args: dict = {}
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    allowed_query_params = []
    for key, value in query_params:
        if key == "sslmode":
            if value and value.lower() not in {"disable", "allow", "prefer"}:
                # asyncpg doesn't accept libpq's sslmode query param directly.
                # `ssl=True` is the closest equivalent to Neon-style sslmode=require.
                normalized_connect_args["ssl"] = True
            continue
        if key == "channel_binding":
            continue
        allowed_query_params.append((key, value))
    normalized_url = urlunparse(parsed._replace(query=urlencode(allowed_query_params, doseq=True)))
    return normalized_url, normalized_connect_args

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
asyncpg_url, normalized_connect_args = _normalize_asyncpg_url(settings.DATABASE_URL)
connect_args.update(normalized_connect_args)
engine: AsyncEngine = create_async_engine(
    asyncpg_url,
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
