"""TikTok Trending Feed API endpoint."""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.core import get_settings, logger
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/trending/tiktok")
async def get_tiktok_trending(
    count: Optional[int] = 20,
    user: dict = Depends(get_current_user),
):
    """
    Get TikTok trending feed.
    
    Returns the current trending videos from TikTok.
    Used for the home page marquee display.
    """
    settings = get_settings()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{settings.SCRAPECREATORS_BASE_URL}/v1/tiktok/get-trending-feed",
                headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response and normalize for frontend
            items = []
            raw_items = data.get("data", {}).get("items", [])
            
            for item in raw_items[:count]:
                if not item:
                    continue
                    
                video_obj = item.get("video", {})
                author = item.get("author", {})
                stats = item.get("statistics", {})
                
                # Get cover/thumbnail URL
                cover_urls = video_obj.get("cover", {}).get("url_list", [])
                thumbnail = cover_urls[0] if cover_urls else None
                
                # Get animated cover (better for hover effect)
                dynamic_cover_urls = video_obj.get("dynamic_cover", {}).get("url_list", [])
                dynamic_cover = dynamic_cover_urls[0] if dynamic_cover_urls else None
                
                # Get video play URL
                play_urls = video_obj.get("play_addr", {}).get("url_list", [])
                video_url = play_urls[0] if play_urls else None
                
                # Author info
                avatar_thumb = author.get("avatar_thumb", {})
                if isinstance(avatar_thumb, dict):
                    avatar_url = avatar_thumb.get("url_list", [None])[0]
                else:
                    avatar_url = avatar_thumb if isinstance(avatar_thumb, str) else None
                
                items.append({
                    "id": item.get("aweme_id") or item.get("id"),
                    "description": item.get("desc", ""),
                    "thumbnail": thumbnail,
                    "dynamicCover": dynamic_cover,
                    "videoUrl": video_url,
                    "duration": video_obj.get("duration", 0),
                    "author": {
                        "id": author.get("uid"),
                        "uniqueId": author.get("unique_id"),
                        "nickname": author.get("nickname"),
                        "avatar": avatar_url,
                    },
                    "stats": {
                        "views": stats.get("play_count", 0),
                        "likes": stats.get("digg_count", 0),
                        "comments": stats.get("comment_count", 0),
                        "shares": stats.get("share_count", 0),
                    },
                })
            
            return {
                "items": items,
                "creditsRemaining": data.get("credits_remaining"),
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"TikTok trending API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch trending videos"
            )
        except Exception as e:
            logger.error(f"TikTok trending API error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch trending videos"
            )
