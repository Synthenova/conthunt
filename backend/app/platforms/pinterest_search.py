"""Pinterest Search platform adapter."""
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


class PinterestSearchAdapter:
    """Adapter for Pinterest search via ScrapeCreators API."""
    
    slug = "pinterest"
    
    async def fetch(
        self,
        client: httpx.AsyncClient,
        query: str,
        params: dict,
    ) -> dict:
        """Fetch Pinterest search results."""
        settings = get_settings()
        
        request_params = {
            "query": query,
        }
        
        if "cursor" in params and params["cursor"]:
            request_params["cursor"] = params["cursor"]
        if params.get("trim") is not None:
            request_params["trim"] = str(params["trim"]).lower()
        
        response = await client.get(
            f"{settings.SCRAPECREATORS_BASE_URL}/v1/pinterest/search",
            params=request_params,
            headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
        )
        response.raise_for_status()
        return response.json()
    
    def parse(self, response_json: dict) -> ParsedPlatformResponse:
        """Parse Pinterest search response into normalized items."""
        items: list[NormalizedItem] = []
        
        data = response_json.get("data", response_json)
        pins = data.get("pins", data.get("results", data.get("items", [])))
        
        for pin in pins:
            if not pin:
                continue
            
            media_urls = []
            
            # Extract image - Pinterest pins have images.orig.url
            images = pin.get("images", {})
            orig_image = images.get("orig", {})
            image_url = orig_image.get("url")
            
            if image_url:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.IMAGE,
                    source_url=image_url,
                ))
            
            # Also check for other image sizes
            for size_key in ["736x", "474x", "236x"]:
                size_img = images.get(size_key, {})
                if size_img.get("url") and not image_url:
                    media_urls.append(MediaUrl(
                        asset_type=AssetType.IMAGE,
                        source_url=size_img["url"],
                    ))
                    break
            
            # Check for video content
            videos = pin.get("videos", {})
            video_list = videos.get("video_list", {})
            if video_list:
                # Get the highest quality video
                for quality in ["V_720P", "V_480P", "V_360P"]:
                    if quality in video_list:
                        video_url = video_list[quality].get("url")
                        if video_url:
                            media_urls.append(MediaUrl(
                                asset_type=AssetType.VIDEO,
                                source_url=video_url,
                            ))
                            break
            
            # Parse metrics
            metrics = {}
            if "repin_count" in pin:
                metrics["repins"] = pin.get("repin_count")
            if "comment_count" in pin:
                metrics["comments"] = pin.get("comment_count")
            if "save_count" in pin:
                metrics["saves"] = pin.get("save_count")
            
            # Get external ID
            external_id = str(pin.get("id", ""))
            if not external_id:
                continue
            
            # Build canonical URL
            canonical_url = f"https://www.pinterest.com/pin/{external_id}/"
            
            # Get pinner info
            pinner = pin.get("pinner", {})
            creator_handle = pinner.get("username")
            
            # Author details
            author_id = pinner.get("id")
            author_name = pinner.get("full_name")
            author_url = f"https://www.pinterest.com/{creator_handle}/" if creator_handle else None
            author_image_url = pinner.get("image_medium_url") or pinner.get("image_small_url") or pinner.get("image_large_url")

            # Determine content type
            content_type = "pin"
            if pin.get("is_video"):
                content_type = "video_pin"
            
            item = NormalizedItem(
                platform="pinterest",
                external_id=external_id,
                content_type=content_type,
                canonical_url=canonical_url,
                title=pin.get("title"),
                primary_text=pin.get("description") or pin.get("title"),
                published_at=None,  # Pinterest doesn't typically expose this
                creator_handle=creator_handle,
                author_id=author_id,
                author_name=author_name,
                author_url=author_url,
                author_image_url=author_image_url,
                metrics=metrics,
                payload={
                    "pinner": {
                        "id": pinner.get("id"),
                        "username": pinner.get("username"),
                        "full_name": pinner.get("full_name"),
                        "image_url": author_image_url,
                    },
                    "board": pin.get("board", {}),
                    "domain": pin.get("domain"),
                    "link": pin.get("link"),
                    "is_video": pin.get("is_video"),
                },
                media_urls=media_urls,
            )
            items.append(item)
        
        # Extract response metadata
        response_meta = {
            "credits_remaining": response_json.get("credits_remaining"),
            "items_count": len(items),
        }
        
        # Extract cursor for pagination
        next_cursor = None
        cursor = data.get("cursor") or data.get("bookmark")
        if cursor:
            next_cursor = {"cursor": cursor}
        
        return ParsedPlatformResponse(
            items=items,
            next_cursor=next_cursor,
            response_meta=response_meta,
            raw_response=response_json,
        )


pinterest_search_adapter = PinterestSearchAdapter()
