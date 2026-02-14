"""Agent runtime initialization.

Creates the async checkpointer and compiled graph at application startup.
"""
import os
from contextlib import asynccontextmanager
from urllib.parse import quote

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.agent.graph import build_graph
from app.core import logger, get_settings


def _parse_prepare_threshold(raw: str | None) -> int | None:
    # For PgBouncer transaction pooling / some Cloud SQL poolers, prepared statements can break:
    # "prepared statement ... does not exist". Using prepare_threshold=None avoids that.
    if raw is None:
        return 0
    v = raw.strip().lower()
    if v in {"none", "null", "nil"}:
        return None
    return int(v)


@asynccontextmanager
async def _async_postgres_saver_cm(
    conn_string: str,
    *,
    schema: str,
    prepare_threshold: int | None,
):
    # Workaround for LangGraph issue: expose psycopg prepare_threshold without relying on
    # AsyncPostgresSaver.from_conn_string() hardcoded defaults.
    conn = await AsyncConnection.connect(
        conn_string,
        autocommit=True,
        prepare_threshold=prepare_threshold,
        row_factory=dict_row,
    )
    try:
        # Avoid libpq "options=" startup parameter (PgBouncer can reject it in transaction mode).
        # Do it as a regular SQL statement instead.
        async with conn.cursor() as cur:
            await cur.execute(f"SET search_path TO {schema}, public;")
        saver = AsyncPostgresSaver(conn)
        yield saver
    finally:
        await conn.close()


async def create_agent_graph(database_url: str):
    """
    Create and return the compiled graph with async checkpointer.
    
    Args:
        database_url: PostgreSQL connection string (e.g., postgresql+psycopg://...)
    
    Returns:
        Tuple of (compiled_graph, saver_context_manager) - 
        The context manager must be cleaned up on shutdown.
    """
    settings = get_settings()
    
    # Convert SQLAlchemy URL format to psycopg format if needed
    # AsyncPostgresSaver expects: postgresql://user:pass@host:port/db
    pg_url = database_url
    if pg_url.startswith("postgresql+psycopg://"):
        pg_url = pg_url.replace("postgresql+psycopg://", "postgresql://")
    elif pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql+asyncpg://", "postgresql://")
    
    schema = settings.DB_SCHEMA
    keepalive_params = (
        "keepalives=1&keepalives_idle=30&keepalives_interval=10&"
        "keepalives_count=5"
    )
    
    # Simple string append (URI query). Keepalives are safe; search_path is set via SQL after connect.
    if "?" in pg_url:
        if not pg_url.endswith(("?", "&")):
            pg_url = f"{pg_url}&"
    else:
        pg_url = f"{pg_url}?"
    # Keep the TCP connection alive so the checkpointer doesn't drop after idle periods.
    pg_url = f"{pg_url}{keepalive_params}"
    
    logger.info(f"Initializing AsyncPostgresSaver checkpointer with schema: {schema}")

    prepare_threshold = _parse_prepare_threshold(os.getenv("LANGGRAPH_PREPARE_THRESHOLD"))
    saver_cm = _async_postgres_saver_cm(pg_url, schema=schema, prepare_threshold=prepare_threshold)
    saver = await saver_cm.__aenter__()
    
    # Create checkpoint tables if they don't exist
    await saver.setup()
    logger.info("Checkpointer tables initialized")
    
    # Build and return the graph
    graph = build_graph(saver)
    logger.info("Agent graph compiled successfully")
    
    return graph, saver_cm
