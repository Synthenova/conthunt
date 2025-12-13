"""Media URL extraction helpers."""
from typing import List

from app.platforms.base import MediaUrl, NormalizedItem


def extract_media_urls(item: NormalizedItem) -> List[MediaUrl]:
    """
    Extract media URLs from a normalized item.
    
    This is a pass-through since media URLs are already extracted
    during parsing. This function exists for any additional
    normalization or filtering that might be needed.
    """
    return item.media_urls


def get_best_media_url(urls: List[MediaUrl], asset_type: str = None) -> MediaUrl | None:
    """
    Get the best media URL from a list, optionally filtered by asset type.
    
    Preference order:
    1. First URL of the specified type
    2. First URL overall if type not specified
    """
    if asset_type:
        filtered = [u for u in urls if u.asset_type.value == asset_type]
        if filtered:
            return filtered[0]
    
    return urls[0] if urls else None


def get_file_extension(url: str, mime_type: str = None) -> str:
    """
    Determine file extension from URL or MIME type.
    """
    # Try to get from URL path
    if "?" in url:
        url = url.split("?")[0]
    
    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "video/mp4": "mp4",
        "video/webm": "webm",
    }
    
    if mime_type and mime_type in ext_map:
        return ext_map[mime_type]
    
    # Common extensions
    if url.endswith(".jpg") or url.endswith(".jpeg"):
        return "jpg"
    elif url.endswith(".png"):
        return "png"
    elif url.endswith(".gif"):
        return "gif"
    elif url.endswith(".webp"):
        return "webp"
    elif url.endswith(".mp4"):
        return "mp4"
    elif url.endswith(".webm"):
        return "webm"
    
    # Default based on common patterns
    if "/video/" in url or "video" in url.lower():
        return "mp4"
    
    return "jpg"  # Default to jpg for images
