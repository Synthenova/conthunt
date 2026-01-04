"""Shared utilities for building content item responses."""
from typing import Optional


def extract_author_from_payload(
    platform: str, 
    payload: dict, 
    creator_handle: Optional[str] = None
) -> dict:
    """
    Extract author information from content item payload based on platform.
    
    Returns a dict with:
    - author_id
    - author_name
    - author_url
    - author_image_url
    """
    author_id = None
    author_name = None
    author_url = None
    author_image_url = None
    
    if platform.startswith("tiktok"):
        auth = payload.get("author", {})
        author_id = auth.get("uid") or auth.get("unique_id")
        author_name = auth.get("nickname")
        author_image_url = auth.get("avatar")
        if not author_image_url:
            thumb = auth.get("avatar_thumb")
            if isinstance(thumb, dict):
                author_image_url = (thumb.get("url_list") or [None])[0]
            elif isinstance(thumb, str):
                author_image_url = thumb
        if creator_handle:
            author_url = f"https://www.tiktok.com/@{creator_handle}"
            
    elif platform == "instagram_reels" or platform == "instagram":
        owner = payload.get("owner", {})
        author_id = owner.get("id")
        author_name = owner.get("full_name")
        author_image_url = owner.get("profile_pic_url")
        if owner.get("username"):
            author_url = f"https://www.instagram.com/{owner['username']}/"
            
    elif platform == "youtube_search" or platform == "youtube":
        channel = payload.get("channel", {})
        author_id = channel.get("id")
        author_name = channel.get("name") or channel.get("title")
        author_image_url = channel.get("thumbnail")
        if channel.get("url"):
            author_url = channel.get("url")
        elif channel.get("handle"):
            author_url = f"https://www.youtube.com/{channel['handle']}"
        
    elif platform == "pinterest_search" or platform == "pinterest":
        pinner = payload.get("pinner", {})
        author_id = pinner.get("id")
        author_name = pinner.get("full_name")
        author_image_url = pinner.get("image_medium_url")
        if pinner.get("username"):
            author_url = f"https://www.pinterest.com/{pinner['username']}/"
    
    return {
        "author_id": author_id,
        "author_name": author_name,
        "author_url": author_url,
        "author_image_url": author_image_url,
    }


def content_item_from_row(row: tuple, offset: int = 0) -> dict:
    """
    Build a content_item dict from a database row tuple.
    
    Expected column order at offset:
        id, platform, external_id, content_type, canonical_url,
        title, primary_text, published_at, creator_handle,
        author_id, author_name, author_url, author_image_url, metrics
    
    Args:
        row: Database result row (tuple)
        offset: Starting index for content_item columns (default 0)
        
    Returns:
        Complete content_item dict with author info from columns
    """
    return {
        "id": row[offset + 0],
        "platform": row[offset + 1],
        "external_id": row[offset + 2],
        "content_type": row[offset + 3],
        "canonical_url": row[offset + 4],
        "title": row[offset + 5],
        "primary_text": row[offset + 6],
        "published_at": row[offset + 7],
        "creator_handle": row[offset + 8],
        "author_id": row[offset + 9],
        "author_name": row[offset + 10],
        "author_url": row[offset + 11],
        "author_image_url": row[offset + 12],
        "metrics": row[offset + 13],
    }
