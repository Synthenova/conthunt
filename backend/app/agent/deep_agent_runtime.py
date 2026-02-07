"""Deep agent runtime initialization with Postgres checkpointer."""
from urllib.parse import quote

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core import logger, get_settings
from app.agent.deep_agent import build_deep_agent


async def create_deep_agent_graph(database_url: str, model_name: str | None = None):
    settings = get_settings()

    pg_url = database_url
    if pg_url.startswith("postgresql+psycopg://"):
        pg_url = pg_url.replace("postgresql+psycopg://", "postgresql://")
    elif pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql+asyncpg://", "postgresql://")

    schema = settings.DB_SCHEMA
    options_param = quote(f"-c search_path={schema},public")
    keepalive_params = (
        "keepalives=1&keepalives_idle=30&keepalives_interval=10&"
        "keepalives_count=5"
    )

    if "?" in pg_url:
        pg_url = f"{pg_url}&options={options_param}"
    else:
        pg_url = f"{pg_url}?options={options_param}"
    pg_url = f"{pg_url}&{keepalive_params}"

    logger.info("Initializing Deep Agent checkpointer with schema: %s", schema)

    saver_cm = AsyncPostgresSaver.from_conn_string(pg_url)
    saver = await saver_cm.__aenter__()
    await saver.setup()
    logger.info("Deep Agent checkpointer tables initialized")

    graph = build_deep_agent(saver, model_name=model_name)
    logger.info("Deep Agent graph compiled successfully")

    return graph, saver_cm
