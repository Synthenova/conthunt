"""API v1 router - aggregates all v1 endpoints."""
from fastapi import APIRouter

from app.api.v1 import search, history, media, boards, twelvelabs

router = APIRouter(prefix="/v1")
router.include_router(search.router, tags=["search"])
router.include_router(history.router, tags=["history"])
router.include_router(media.router, prefix="/media", tags=["media"])
router.include_router(boards.router, prefix="/boards", tags=["boards"])
router.include_router(twelvelabs.router, tags=["video-analysis"])

