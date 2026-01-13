"""Database session and engine management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event, text

from app.core import get_settings

settings = get_settings()

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
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
        # Set search path explicitly for this connection
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
