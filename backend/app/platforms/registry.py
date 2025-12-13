"""Platform adapter registry."""
from typing import Dict

from app.platforms.base import PlatformAdapter
from app.platforms.instagram_reels import instagram_reels_adapter
from app.platforms.tiktok_keyword import tiktok_keyword_adapter
from app.platforms.tiktok_top import tiktok_top_adapter
from app.platforms.youtube_search import youtube_search_adapter
from app.platforms.pinterest_search import pinterest_search_adapter


# Registry mapping slug to adapter instance
PLATFORM_ADAPTERS: Dict[str, PlatformAdapter] = {
    "instagram_reels": instagram_reels_adapter,
    "tiktok_keyword": tiktok_keyword_adapter,
    "tiktok_top": tiktok_top_adapter,
    "youtube": youtube_search_adapter,
    "pinterest": pinterest_search_adapter,
}


def get_adapter(slug: str) -> PlatformAdapter:
    """Get adapter by slug, raises KeyError if not found."""
    return PLATFORM_ADAPTERS[slug]


def get_available_platforms() -> list[str]:
    """Get list of available platform slugs."""
    return list(PLATFORM_ADAPTERS.keys())
