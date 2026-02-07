"""
Conthunt Backend API

FastAPI application with multi-platform content search,
Cloud SQL storage, and GCS media archival.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

import redis.asyncio as redis

from app.core import get_settings, logger
from app.core.logging import setup_logging, get_log_level
from app.core.telemetry import setup_telemetry
from app.db import init_db, close_db
from app.realtime.stream_hub import StreamFanoutHub
from app.api import v1_router
from app.agent.runtime import create_agent_graph
from app.llm.gateway import init_gateway

setup_logging(get_log_level())
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.debug("Starting Conthunt backend...")
    try:
        await init_db()
        logger.debug("Database connection verified")
        
        # Use BlockingConnectionPool to wait for connections instead of failing
        from redis.asyncio.connection import BlockingConnectionPool
        redis_pool = BlockingConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            timeout=10.0,  # Wait up to 10s for a connection
            decode_responses=True,
        )
        app.state.redis = redis.Redis(connection_pool=redis_pool)
        max_conn = getattr(app.state.redis.connection_pool, "max_connections", None)
        logger.info("Redis client initialized (max_connections=%s)", max_conn)
        init_gateway(app.state.redis)
        app.state.stream_hub = StreamFanoutHub(app.state.redis, logger)
        await app.state.stream_hub.start()
        logger.debug("Stream hub initialized")
        
        # Initialize agent graph with Postgres checkpointer
        graph, saver_cm = await create_agent_graph(settings.DATABASE_URL)
        app.state.agent_graph = graph
        app.state._agent_saver_cm = saver_cm
        logger.debug("Agent graph initialized with Postgres checkpointer")
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.debug("Shutting down Conthunt backend...")
    if hasattr(app.state, "stream_hub"):
        await app.state.stream_hub.stop()
        logger.debug("Stream hub stopped")
    if hasattr(app.state, "redis"):
        await app.state.redis.close()
        logger.debug("Redis client closed")
    if hasattr(app.state, '_agent_saver_cm'):
        await app.state._agent_saver_cm.__aexit__(None, None, None)
        logger.debug("Agent checkpointer closed")
    if hasattr(app.state, '_deep_agent_saver_cm'):
        await app.state._deep_agent_saver_cm.__aexit__(None, None, None)
        logger.debug("Deep agent checkpointer closed")
    await close_db()
    logger.debug("Database connections closed")


app = FastAPI(
    title="Conthunt API",
    description="Multi-platform content search and archival API",
    version="1.0.0",
    lifespan=lifespan,
)

setup_telemetry(app)

# Honor X-Forwarded-* headers from Cloud Run so redirects keep HTTPS.
# app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://conthunt-frontend-976912795426.us-central1.run.app",
        "https://conthunt-lp-976912795426.us-central1.run.app",
        "https://conthunt-frontend-785174409154.us-central1.run.app",        
        "https://agent.conthunt.app",
        "https://dev.agent.conthunt.app",
        "https://conthunt.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"ok": True, "service": "conthunt-backend"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Conthunt API",
        "version": "1.0.0",
        "docs": "/docs",
    }
