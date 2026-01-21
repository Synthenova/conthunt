"""YouTube Trending Feed API endpoint."""
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List, Literal

from app.core import get_settings, logger
from app.core.redis_client import get_app_redis
from app.auth import get_current_user
import redis.asyncio as redis

from app.agent.model_factory import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

router = APIRouter()


async def get_redis_client(request: Request) -> redis.Redis:
    """Helper to get redis client from app state or create new one."""
    return get_app_redis(request)


@router.get("/trending/youtube")
async def get_youtube_trending(
    request: Request,
    count: Optional[int] = 20,
    user: dict = Depends(get_current_user),
):
    """
    Get YouTube Shorts trending feed.
    
    Returns the current trending shorts from YouTube.
    Cached for 12 hours to minimize API costs.
    """
    settings = get_settings()
    redis_client = await get_redis_client(request)
    cache_key = "trending:youtube:feed"
    
    # Try cache first
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data)
        except Exception:
            pass  # Fallback to fetch if cache invalid

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                "https://api.scrapecreators.com/v1/youtube/shorts/trending",
                headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response and normalize for frontend
            items = []
            raw_shorts = data.get("shorts", [])
            
            for item in raw_shorts:
                if not item:
                    continue
                
                # Normalize to MediaCard format
                channel = item.get("channel", {})
                
                items.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "thumbnail": item.get("thumbnail"),
                    "videoUrl": item.get("url"), # MediaCard handles YouTube URLs
                    "duration": item.get("durationMs", 0) / 1000 if item.get("durationMs") else 0,
                    "author": {
                        "id": channel.get("id"),
                        "uniqueId": channel.get("handle"),
                        "nickname": channel.get("title"),
                        "avatar": None, # API doesn't seem to return avatar in this endpoint
                    },
                    "creator_name": channel.get("title"), # MediaCard compatibility
                    "creator_image": None,
                    "stats": {
                        "views": item.get("viewCountInt", 0),
                        "likes": item.get("likeCountInt", 0),
                        "comments": item.get("commentCountInt", 0),
                        "shares": 0,
                    },
                    "platform": "youtube",
                })
            
            result = {
                "items": items[:count] if count else items,
                "cached": False,
            }

            # Cache for 12 hours (43200 seconds)
            await redis_client.setex(cache_key, 43200, json.dumps({**result, "cached": True}))
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"YouTube trending API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch trending videos"
            )
        except Exception as e:
            logger.error(f"YouTube trending API error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch trending videos"
            )


@router.get("/trending/tiktok")
async def get_tiktok_trending(
    request: Request,
    count: Optional[int] = 20,
    user: dict = Depends(get_current_user),
):
    """
    Get TikTok trending feed.
    
    Returns the current trending videos from TikTok.
    Cached for 12 hours.
    """
    settings = get_settings()
    redis_client = await get_redis_client(request)
    cache_key = "trending:tiktok:feed:v3"  # Bump cache version for new format
    
    # Helper to proxy URLs through our backend to avoid CORS/HEIC issues
    # Uses API_BASE_URL from settings instead of request.base_url to work in prod
    def proxify(url: str | None) -> str | None:
        return url
        if not url:
            return None
        import urllib.parse
        encoded_url = urllib.parse.quote(url)
        return f"{settings.API_BASE_URL}/v1/media/proxy?url={encoded_url}"
    
    # Helper to apply proxification to cached/fresh items at response time
    def proxify_items(items: list) -> list:
        for item in items:
            if item.get("_raw_thumbnail"):
                item["thumbnail_url"] = proxify(item["_raw_thumbnail"])
            if item.get("_raw_avatar"):
                item["author"]["avatar"] = proxify(item["_raw_avatar"])
                item["creator_image"] = proxify(item["_raw_avatar"])
        return items
    
    # Try cache first
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        try:
            data = json.loads(cached_data)
            # Proxify URLs at response time
            data["items"] = proxify_items(data["items"])
            return data
        except Exception:
            pass

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Using defaults: region=US
            response = await client.get(
                "https://api.scrapecreators.com/v1/tiktok/get-trending-feed?region=US",
                headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
            )
            response.raise_for_status()
            data = response.json()
            
            items = []
            aweme_list = data.get("aweme_list", [])

            for item in aweme_list:
                if not item:
                    continue
                
                # Extract fields
                video_data = item.get("video", {})
                author_data = item.get("author", {})
                stats = item.get("statistics", {})
                
                # Get raw URLs (picking first valid one) - store raw, proxify later
                raw_cover_url = None
                if video_data.get("cover", {}).get("url_list"):
                    raw_cover_url = video_data["cover"]["url_list"][0]
                
                video_url = None
                if video_data.get("play_addr", {}).get("url_list"):
                    video_url = video_data["play_addr"]["url_list"][0]
                
                raw_avatar_url = None
                if author_data.get("avatar_medium", {}).get("url_list"):
                    raw_avatar_url = author_data["avatar_medium"]["url_list"][0]
                elif author_data.get("avatar_thumb", {}).get("url_list"):
                    raw_avatar_url = author_data["avatar_thumb"]["url_list"][0]

                items.append({
                    "id": item.get("aweme_id"),
                    "title": item.get("desc"),
                    # Store raw URLs for caching, will be proxified at response time
                    "_raw_thumbnail": raw_cover_url,
                    "_raw_avatar": raw_avatar_url,
                    "thumbnail_url": None,  # Filled by proxify_items
                    "video_url": video_url,
                    "duration": 0,
                    "author": {
                        "id": author_data.get("uid"),
                        "uniqueId": author_data.get("unique_id"),
                        "nickname": author_data.get("nickname"),
                        "avatar": None,  # Filled by proxify_items
                    },
                    "creator_name": author_data.get("nickname"),
                    "creator_image": None,  # Filled by proxify_items
                    "view_count": stats.get("play_count", 0),
                    "like_count": stats.get("digg_count", 0),
                    "comment_count": stats.get("comment_count", 0),
                    "share_count": stats.get("share_count", 0),
                    "platform": "tiktok",
                })
            
            result = {
                "items": items[:count] if count else items,
                "cached": False,
            }

            # Cache for 12 hours - store with raw URLs
            await redis_client.setex(cache_key, 43200, json.dumps({**result, "cached": True}))
            
            # Proxify URLs before returning
            result["items"] = proxify_items(result["items"])
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"TikTok trending API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch trending TikToks"
            )
        except Exception as e:
            logger.error(f"TikTok trending API error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch trending TikToks"
            )


class TrendingNiche(BaseModel):
    trend: Literal['up1', 'up2', 'down1', 'down2'] = Field(
        description="Trend direction: up2 (surging), up1 (rising), down1 (cooling), down2 (fading)"
    )
    keyword: str = Field(description="The niche name/keyword")
    hashtags: List[str] = Field(description="List of 2-3 relevant hashtags")


class TrendingNichesResponse(BaseModel):
    niches: List[TrendingNiche]


@router.get("/trending/niches")
async def get_trending_niches(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Get global top trending niches using AI + Google Search.
    
    Returns a list of structured trending niches.
    Cached for 12 hours.
    """
    settings = get_settings()
    redis_client = await get_redis_client(request)
    cache_key = "trending:niches:global"
    
    # Try cache first
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data)
        except Exception:
            pass

    try:
        # Init model with Google Search
        llm = init_chat_model("google/gemini-3-pro-preview")
        llm = llm.bind_tools([{"google_search": {}}])
        structured_llm = llm.with_structured_output(TrendingNichesResponse)
        
        prompt = "global ranking of top niches name and hashtag. Find at least 15 items to ensure we have enough good ones."
        
        response = await structured_llm.ainvoke([
            SystemMessage(content="You are a trend hunter. use google search to find real-time global trending niches."),
            HumanMessage(content=prompt)
        ])
        
        logger.info(f"Generated {len(response.niches)} trending niches")
        
        result = []
        for niche in response.niches:
             result.append(niche.model_dump())
             
        # Cache for 12 hours (43200 seconds)
        await redis_client.setex(cache_key, 43200, json.dumps(result))
        
        return result

    except Exception as e:
        logger.error(f"Trending niches generation failed: {e}")
        # Return fallback or empty if it fails and no cache
        return []
