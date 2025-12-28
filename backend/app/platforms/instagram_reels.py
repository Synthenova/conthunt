"""Instagram Reels platform adapter."""
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


class InstagramReelsAdapter:
    """Adapter for Instagram Reels search via ScrapeCreators API."""
    
    slug = "instagram_reels"
    
    async def fetch(
        self,
        client: httpx.AsyncClient,
        query: str,
        params: dict,
    ) -> dict:
        """Fetch Instagram reels search results."""
        settings = get_settings()
        
        request_params = {
            "query": query,
            "amount": params.get("amount", 20),
        }
        
        response = await client.get(
            f"{settings.SCRAPECREATORS_BASE_URL}/v1/instagram/reels/search",
            params=request_params,
            headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
        )
        response.raise_for_status()
        return response.json()
    
    def parse(self, response_json: dict) -> ParsedPlatformResponse:
        """Parse Instagram reels response into normalized items."""
        items: list[NormalizedItem] = []
        
        # Handle different response structures
        data = response_json.get("data", response_json)
        reels = data.get("reels", data.get("items", []))
        
        for reel in reels:
            media_urls = []
            
            # Extract thumbnail URLs
            thumbnail_src = reel.get("thumbnail_src")
            if thumbnail_src:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.THUMBNAIL,
                    source_url=thumbnail_src,
                ))
            
            display_url = reel.get("display_url")
            if display_url and display_url != thumbnail_src:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.IMAGE,
                    source_url=display_url,
                ))
            
            # Extract video URL
            video_url = reel.get("video_url")
            if video_url:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.VIDEO,
                    source_url=video_url,
                ))
            
            # Parse published timestamp
            published_at = None
            taken_at = reel.get("taken_at_timestamp") or reel.get("taken_at")
            if taken_at:
                try:
                    published_at = datetime.fromtimestamp(int(taken_at))
                except (ValueError, TypeError):
                    pass
            
            # Extract metrics
            metrics = {}
            if "video_view_count" in reel:
                metrics["views"] = reel.get("video_view_count")
            elif "view_count" in reel:
                metrics["views"] = reel.get("view_count")

            if "video_play_count" in reel:
                metrics["plays"] = reel.get("video_play_count")
            elif "play_count" in reel:
                metrics["plays"] = reel.get("play_count")

            if "like_count" in reel:
                metrics["likes"] = reel.get("like_count")
            if "comment_count" in reel:
                metrics["comments"] = reel.get("comment_count")
            
            # Get external ID
            external_id = str(reel.get("pk") or reel.get("id") or reel.get("shortcode", ""))
            if not external_id:
                continue
            
            # Build canonical URL
            shortcode = reel.get("shortcode") or reel.get("code")
            canonical_url = f"https://www.instagram.com/reel/{shortcode}/" if shortcode else None
            
            # Get creator info
            owner = reel.get("owner", {}) or reel.get("user", {})
            creator_handle = owner.get("username")
            
            # Author details
            author_id = owner.get("id")
            author_name = owner.get("full_name")
            author_url = f"https://www.instagram.com/{creator_handle}/" if creator_handle else None
            author_image_url = owner.get("profile_pic_url")
            
            item = NormalizedItem(
                platform="instagram",
                external_id=external_id,
                content_type="reel",
                canonical_url=canonical_url,
                title=None,
                primary_text=reel.get("caption") or (reel.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text")),
                published_at=published_at,
                creator_handle=creator_handle,
                author_id=author_id,
                author_name=author_name,
                author_url=author_url,
                author_image_url=author_image_url,
                metrics=metrics,
                payload={
                    "shortcode": shortcode,
                    "owner": owner,
                    "dimensions": reel.get("dimensions"),
                    "is_video": reel.get("is_video", True),
                },
                media_urls=media_urls,
            )
            items.append(item)
        
        # Extract response metadata
        response_meta = {
            "credits_remaining": response_json.get("credits_remaining"),
            "items_count": len(items),
        }
        
        # Extract cursor if present
        next_cursor = None
        cursor = response_json.get("cursor") or data.get("end_cursor")
        if cursor:
            next_cursor = {"cursor": cursor}
        
        return ParsedPlatformResponse(
            items=items,
            next_cursor=next_cursor,
            response_meta=response_meta,
            raw_response=response_json,
        )


instagram_reels_adapter = InstagramReelsAdapter()
