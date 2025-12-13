"""API v1 router - aggregates all v1 endpoints."""
from fastapi import APIRouter

from app.api.v1.search import router as search_router
from app.api.v1.history import router as history_router
from app.api.v1.media import router as media_router

router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(search_router, tags=["search"])
router.include_router(history_router, tags=["history"])
router.include_router(media_router, tags=["media"])
