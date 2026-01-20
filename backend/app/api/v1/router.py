"""API v1 router - aggregates all v1 endpoints."""
from fastapi import APIRouter

from app.api.v1 import (
    search,
    history,
    media,
    boards,
    twelvelabs,
    chats,
    analysis,
    tasks,
    user,
    waitlist,
    auth,
    billing,
    webhooks,
    streak,
    onboarding,
    feedback,
    trending,
)

router = APIRouter(prefix="/v1")
router.include_router(auth.router, tags=["auth"])  # Auth sync - no auth required
router.include_router(search.router, tags=["search"])
router.include_router(history.router, tags=["history"])
router.include_router(media.router, prefix="/media", tags=["media"])
router.include_router(boards.router, prefix="/boards", tags=["boards"])
router.include_router(twelvelabs.router, prefix="/twelvelabs", tags=["video-analysis"])
router.include_router(analysis.router, tags=["video-analysis"])  # No prefix - endpoint is /v1/video-analysis/{id}
router.include_router(chats.router, prefix="/chats", tags=["chats"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])  # New Cloud Tasks handler (e.g. /v1/tasks/...)
router.include_router(user.router, tags=["user"])
router.include_router(waitlist.router, tags=["waitlist"])
router.include_router(billing.router, tags=["billing"])
router.include_router(webhooks.router, tags=["webhooks"])
router.include_router(streak.router, tags=["streak"])
router.include_router(onboarding.router, tags=["onboarding"])
router.include_router(feedback.router, tags=["feedback"])
router.include_router(trending.router, tags=["trending"])

