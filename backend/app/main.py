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

from upstash_redis.asyncio import Redis

from app.core import get_settings, logger
from app.core.logging import setup_logging, get_log_level
from app.core.telemetry import setup_telemetry
from app.db import init_db, close_db
from app.api import v1_router
from app.api.v1.webhooks import router as dodo_webhooks_router
from app.middleware.telemetry_context import TelemetryContextMiddleware
from app.agent.runtime import create_agent_graph
from app.integrations.langfuse_client import flush_langfuse
from app.llm.global_rate_limiter import LlmRateLimited


setup_logging(get_log_level())
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.debug("Starting Conthunt backend...")
    logger.info(
        "Deep Research config: model=%s | task_enqueue: gemini_batch=%s media_batch=%s search_batch=%s max_attempts=%s",
        settings.DEEP_RESEARCH_MODEL,
        settings.GEMINI_TASK_ENQUEUE_BATCH_SIZE,
        settings.MEDIA_DOWNLOAD_ENQUEUE_BATCH_SIZE,
        settings.SEARCH_ENQUEUE_BATCH_SIZE,
        settings.TASK_WORKER_MAX_ATTEMPTS,
    )
    try:
        await init_db()
        logger.debug("Database connection verified")
        app.state.redis = Redis.from_env(read_your_writes=True)
        logger.info("Upstash Redis client initialized")

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
app.include_router(dodo_webhooks_router)


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
