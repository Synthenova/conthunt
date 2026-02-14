"""
Conthunt Backend API

FastAPI application with multi-platform content search,
Cloud SQL storage, and GCS media archival.
"""
from contextlib import asynccontextmanager
import math

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
from app.middleware.telemetry_context import TelemetryContextMiddleware
from app.agent.runtime import create_agent_graph
from app.integrations.langfuse_client import flush_langfuse
from app.db.db_semaphore import (
    DBSemaphore,
    SemaphoreConfig,
    db_kind_override,
    set_global_db_semaphore,
)
from app.llm.global_rate_limiter import LlmRateLimited


setup_logging(get_log_level())
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.debug("Starting Conthunt backend...")
    logger.info(
        "Deep Research config: analysis_concurrency=%s, search_concurrency=%s, model=%s",
        settings.DEEP_RESEARCH_ANALYSIS_CONCURRENCY,
        settings.DEEP_RESEARCH_SEARCH_CONCURRENCY,
        settings.DEEP_RESEARCH_MODEL,
    )
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
            # Managed Redis/proxies can silently close idle sockets; health checks prevent
            # handing out dead connections from the pool.
            health_check_interval=30,
            socket_keepalive=True,
        )
        app.state.redis = redis.Redis(connection_pool=redis_pool)
        max_conn = getattr(app.state.redis.connection_pool, "max_connections", None)
        logger.info("Redis client initialized (max_connections=%s)", max_conn)

        # Initialize global DB semaphore (fail-open if anything goes wrong).
        if getattr(settings, "DB_SEMAPHORE_ENABLED", False):
            try:
                cfg = SemaphoreConfig(
                    app_env=settings.APP_ENV,
                    key_prefix=settings.DB_SEM_KEY_PREFIX,
                    ttl_ms=settings.DB_SEM_TTL_MS,
                    api_limit=settings.DB_SEM_API_LIMIT,
                    tasks_limit=settings.DB_SEM_TASKS_LIMIT,
                )
                sem = DBSemaphore(app.state.redis, cfg)
                await sem.init()
                app.state.db_semaphore = sem
                set_global_db_semaphore(sem)
                logger.info(
                    "DB semaphore enabled (env=%s api_limit=%s tasks_limit=%s ttl_ms=%s)",
                    settings.APP_ENV,
                    settings.DB_SEM_API_LIMIT,
                    settings.DB_SEM_TASKS_LIMIT,
                    settings.DB_SEM_TTL_MS,
                )
            except Exception as exc:
                logger.warning("DB semaphore init failed (fail-open): %s", exc, exc_info=True)
                app.state.db_semaphore = None
                set_global_db_semaphore(None)
        else:
            app.state.db_semaphore = None
            set_global_db_semaphore(None)

        # StreamFanoutHub uses a BLOCKING xread (up to 10s per call) which holds
        # a Redis connection for the entire block duration.  Give it a dedicated
        # small pool so it can never starve the main pool used by the DB
        # semaphore and other short-lived commands.
        stream_pool = BlockingConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=2,
            timeout=10.0,
            decode_responses=True,
            health_check_interval=30,
            socket_keepalive=True,
        )
        app.state.stream_redis = redis.Redis(connection_pool=stream_pool)

        app.state.stream_hub = StreamFanoutHub(app.state.stream_redis, logger)
        await app.state.stream_hub.start()
        logger.debug("Stream hub initialized")

        # Centralized writer/outbox removed.
        
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
    if hasattr(app.state, "stream_redis"):
        await app.state.stream_redis.close()
        logger.debug("Stream Redis client closed")
    if hasattr(app.state, '_agent_saver_cm'):
        await app.state._agent_saver_cm.__aexit__(None, None, None)
        logger.debug("Agent checkpointer closed")
    if hasattr(app.state, '_deep_agent_saver_cm'):
        await app.state._deep_agent_saver_cm.__aexit__(None, None, None)
        logger.debug("Deep agent checkpointer closed")
    await close_db()
    logger.debug("Database connections closed")
    try:
        flush_langfuse(reason="app_shutdown")
    except Exception:
        pass


app = FastAPI(
    title="Conthunt API",
    description="Multi-platform content search and archival API",
    version="1.0.0",
    lifespan=lifespan,
)

setup_telemetry(app)

app.add_middleware(TelemetryContextMiddleware)


@app.exception_handler(LlmRateLimited)
async def _llm_rate_limited_handler(request, exc: LlmRateLimited):
    from fastapi.responses import JSONResponse

    headers: dict[str, str] = {}
    if exc.retry_after_s is not None:
        try:
            headers["Retry-After"] = str(int(math.ceil(float(exc.retry_after_s))))
        except Exception:
            pass

    return JSONResponse(
        status_code=429,
        headers=headers,
        content={
            "error": "LLM_RATE_LIMITED",
            "kind": exc.kind,
            "model": exc.model_key,
            "route": exc.route,
        },
    )

# Middleware: mark DB work as "tasks" for /v1/tasks/*, else "api".
@app.middleware("http")
async def _db_kind_middleware(request, call_next):
    kind = "tasks" if request.url.path.startswith("/v1/tasks/") else "api"
    with db_kind_override(kind):
        return await call_next(request)

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
