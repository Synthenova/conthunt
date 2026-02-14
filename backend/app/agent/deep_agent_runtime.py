"""Deep agent runtime initialization with Postgres checkpointer."""
import os
from contextlib import asynccontextmanager
from urllib.parse import quote

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.core import logger, get_settings
from app.agent.deep_agent import build_deep_agent


def _parse_prepare_threshold(raw: str | None) -> int | None:
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
    conn = await AsyncConnection.connect(
        conn_string,
        autocommit=True,
        prepare_threshold=prepare_threshold,
        row_factory=dict_row,
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute(f"SET search_path TO {schema}, public;")
        saver = AsyncPostgresSaver(conn)
        yield saver
    finally:
        await conn.close()


async def create_deep_agent_graph(database_url: str, model_name: str | None = None):
    settings = get_settings()

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

    if "?" in pg_url:
        if not pg_url.endswith(("?", "&")):
            pg_url = f"{pg_url}&"
    else:
        pg_url = f"{pg_url}?"
    pg_url = f"{pg_url}{keepalive_params}"

    logger.info("Initializing Deep Agent checkpointer with schema: %s", schema)

    prepare_threshold = _parse_prepare_threshold(os.getenv("LANGGRAPH_PREPARE_THRESHOLD"))
    saver_cm = _async_postgres_saver_cm(pg_url, schema=schema, prepare_threshold=prepare_threshold)
    saver = await saver_cm.__aenter__()
    await saver.setup()
    logger.info("Deep Agent checkpointer tables initialized")

    graph = build_deep_agent(saver, model_name=model_name)
    logger.info("Deep Agent graph compiled successfully")

    return graph, saver_cm
