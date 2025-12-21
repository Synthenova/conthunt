"""
Conthunt Backend API

FastAPI application with multi-platform content search,
Cloud SQL storage, and GCS media archival.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import get_settings, logger
from app.db import init_db, close_db
from app.api import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.info("Starting Conthunt backend...")
    try:
        await init_db()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Conthunt backend...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title="Conthunt API",
    description="Multi-platform content search and archival API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://conthunt-frontend-976912795426.us-central1.run.app",
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
