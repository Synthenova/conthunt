"""Agent runtime initialization.

Creates the async checkpointer and compiled graph at application startup.
"""
from urllib.parse import quote

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.graph import build_graph
from app.core import logger, get_settings


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
    
    # Add search_path option so checkpointer uses correct schema
    schema = settings.DB_SCHEMA
    options_param = quote(f"-c search_path={schema},public")
    keepalive_params = (
        "keepalives=1&keepalives_idle=30&keepalives_interval=10&"
        "keepalives_count=5"
    )
    
    # Simple string append to avoid urlparse issues with bracketed IPv4
    if "?" in pg_url:
        pg_url = f"{pg_url}&options={options_param}"
    else:
        pg_url = f"{pg_url}?options={options_param}"
    # Keep the TCP connection alive so the checkpointer doesn't drop after idle periods
    pg_url = f"{pg_url}&{keepalive_params}"
    
    logger.info(f"Initializing AsyncPostgresSaver checkpointer with schema: {schema}")
    
    # Create the async saver context manager
    saver_cm = AsyncPostgresSaver.from_conn_string(pg_url)
    saver = await saver_cm.__aenter__()
    
    # Create checkpoint tables if they don't exist
    await saver.setup()
    logger.info("Checkpointer tables initialized")
    
    # Build and return the graph
    graph = build_graph(saver)
    logger.info("Agent graph compiled successfully")
    
    return graph, saver_cm
