"""YouTube Search platform adapter."""
from datetime import datetime
from typing import Optional

import httpx

from app.core import get_settings, logger
from app.platforms.base import (
    AssetType,
    MediaUrl,
    NormalizedItem,
    ParsedPlatformResponse,
)


class YouTubeSearchAdapter:
    """Adapter for YouTube search via ScrapeCreators API."""
    
    slug = "youtube"
    
    async def fetch(
        self,
        client: httpx.AsyncClient,
        query: str,
        params: dict,
    ) -> dict:
        """Fetch YouTube search results."""
        settings = get_settings()
        
        request_params = {
            "query": query,
        }
        
        if "uploadDate" in params:
            request_params["uploadDate"] = params["uploadDate"]
        if "sortBy" in params:
            request_params["sortBy"] = params["sortBy"]
        if "filter" in params:
            request_params["filter"] = params["filter"]
        if "continuationToken" in params:
            request_params["continuationToken"] = params["continuationToken"]
        if params.get("includeExtras") is not None:
            request_params["includeExtras"] = str(params["includeExtras"]).lower()
        
        response = await client.get(
            f"{settings.SCRAPECREATORS_BASE_URL}/v1/youtube/search",
            params=request_params,
            headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
        )
        response.raise_for_status()
        return response.json()
    
    def parse(self, response_json: dict) -> ParsedPlatformResponse:
        """Parse YouTube search response into normalized items."""
        items: list[NormalizedItem] = []
        
        data = response_json.get("data", response_json)
        
        # YouTube response can have both 'videos' and 'shelves.items' (shorts)
        all_videos = []
        
        # Direct videos
        videos = data.get("videos", [])
        all_videos.extend(videos)
        
        # Shelves (shorts)
        shelves = data.get("shelves", [])
        for shelf in shelves:
            shelf_items = shelf.get("items", [])
            all_videos.extend(shelf_items)
        
        # Also check for 'items' directly
        if not all_videos:
            all_videos = data.get("items", [])
        
        for video in all_videos:
            if not video:
                continue
            
            media_urls = []
            
            # Extract thumbnail
            thumbnail = video.get("thumbnail")
            if thumbnail:
                if isinstance(thumbnail, str):
                    media_urls.append(MediaUrl(
                        asset_type=AssetType.THUMBNAIL,
                        source_url=thumbnail,
                    ))
                elif isinstance(thumbnail, dict):
                    thumb_url = thumbnail.get("url") or thumbnail.get("static")
                    if thumb_url:
                        media_urls.append(MediaUrl(
                            asset_type=AssetType.THUMBNAIL,
                            source_url=thumb_url,
                        ))
            
            # Thumbnails array
            thumbnails = video.get("thumbnails", [])
            for thumb in thumbnails:
                if isinstance(thumb, dict) and thumb.get("url"):
                    media_urls.append(MediaUrl(
                        asset_type=AssetType.THUMBNAIL,
                        source_url=thumb["url"],
                    ))
                    break  # Just take the first one
            
            # Parse published date
            published_at = None
            published_text = video.get("publishedAt") or video.get("publishedText")
            # YouTube often returns relative time, we'll store what we get
            
            # Extract metrics
            metrics = {}
            if "viewCount" in video:
                metrics["views"] = video.get("viewCount")
            elif "views" in video:
                metrics["views"] = video.get("views")
            if "likeCount" in video:
                metrics["likes"] = video.get("likeCount")
            
            # Get external ID
            external_id = video.get("videoId") or video.get("id", "")
            if not external_id:
                continue
            
            # Determine content type
            content_type = "video"
            if video.get("isShort") or (data.get("type") == "shorts"):
                content_type = "short"
            
            # Build canonical URL
            canonical_url = f"https://www.youtube.com/watch?v={external_id}"
            if content_type == "short":
                canonical_url = f"https://www.youtube.com/shorts/{external_id}"
            
            # Get channel info
            channel = video.get("channel", {})
            creator_handle = channel.get("name") or video.get("channelTitle")
            
            item = NormalizedItem(
                platform="youtube",
                external_id=external_id,
                content_type=content_type,
                canonical_url=canonical_url,
                title=video.get("title"),
                primary_text=video.get("description") or video.get("title"),
                published_at=published_at,
                creator_handle=creator_handle,
                metrics=metrics,
                payload={
                    "channel": {
                        "id": channel.get("id") or video.get("channelId"),
                        "name": channel.get("name") or video.get("channelTitle"),
                        "url": channel.get("url"),
                    },
                    "duration": video.get("duration"),
                    "durationText": video.get("durationText"),
                    "isLive": video.get("isLive"),
                    "isShort": video.get("isShort"),
                },
                media_urls=media_urls,
            )
            items.append(item)
        
        # Extract response metadata
        response_meta = {
            "credits_remaining": response_json.get("credits_remaining"),
        }
        
        # Extract continuation token
        next_cursor = None
        continuation = data.get("continuationToken") or data.get("continuation")
        if continuation:
            next_cursor = {"continuationToken": continuation}
        
        return ParsedPlatformResponse(
            items=items,
            next_cursor=next_cursor,
            response_meta=response_meta,
            raw_response=response_json,
        )


youtube_search_adapter = YouTubeSearchAdapter()
