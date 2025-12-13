"""TikTok Keyword Search platform adapter."""
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


class TikTokKeywordAdapter:
    """Adapter for TikTok keyword search via ScrapeCreators API."""
    
    slug = "tiktok_keyword"
    
    async def fetch(
        self,
        client: httpx.AsyncClient,
        query: str,
        params: dict,
    ) -> dict:
        """Fetch TikTok keyword search results."""
        settings = get_settings()
        
        request_params = {
            "query": query,
            "date_posted": params.get("date_posted", "all"),
            "sort_by": params.get("sort_by", "relevance"),
            "region": params.get("region", "US"),
        }
        
        if "cursor" in params:
            request_params["cursor"] = params["cursor"]
        if params.get("trim") is not None:
            request_params["trim"] = str(params["trim"]).lower()
        
        response = await client.get(
            f"{settings.SCRAPECREATORS_BASE_URL}/v1/tiktok/search/keyword",
            params=request_params,
            headers={"x-api-key": settings.SCRAPECREATORS_API_KEY},
        )
        response.raise_for_status()
        return response.json()
    
    def parse(self, response_json: dict) -> ParsedPlatformResponse:
        """Parse TikTok keyword search response into normalized items."""
        items: list[NormalizedItem] = []
        
        # TikTok keyword response structure: search_item_list[].aweme_info
        data = response_json.get("data", response_json)
        search_items = data.get("search_item_list", data.get("items", []))
        
        for search_item in search_items:
            # Data is nested under aweme_info
            aweme = search_item.get("aweme_info", search_item)
            if not aweme:
                continue
            
            media_urls = []
            
            # Extract cover/thumbnail from video object
            video_obj = aweme.get("video", {})
            
            # Cover images
            cover_urls = video_obj.get("cover", {}).get("url_list", [])
            if cover_urls:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.COVER,
                    source_url=cover_urls[0],
                    source_url_list=cover_urls,
                ))
            
            # Dynamic cover
            dynamic_cover_urls = video_obj.get("dynamic_cover", {}).get("url_list", [])
            if dynamic_cover_urls and dynamic_cover_urls != cover_urls:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.THUMBNAIL,
                    source_url=dynamic_cover_urls[0],
                    source_url_list=dynamic_cover_urls,
                ))
            
            # Video play URLs
            play_urls = video_obj.get("play_addr", {}).get("url_list", [])
            if play_urls:
                media_urls.append(MediaUrl(
                    asset_type=AssetType.VIDEO,
                    source_url=play_urls[0],
                    source_url_list=play_urls,
                ))
            
            # Parse published timestamp
            published_at = None
            create_time = aweme.get("create_time")
            if create_time:
                try:
                    published_at = datetime.fromtimestamp(int(create_time))
                except (ValueError, TypeError):
                    pass
            
            # Extract metrics from statistics
            stats = aweme.get("statistics", {})
            metrics = {}
            if "play_count" in stats:
                metrics["views"] = stats.get("play_count")
            if "digg_count" in stats:
                metrics["likes"] = stats.get("digg_count")
            if "comment_count" in stats:
                metrics["comments"] = stats.get("comment_count")
            if "share_count" in stats:
                metrics["shares"] = stats.get("share_count")
            
            # Get external ID
            external_id = str(aweme.get("aweme_id") or aweme.get("id", ""))
            if not external_id:
                continue
            
            # Get author info
            author = aweme.get("author", {})
            creator_handle = author.get("unique_id") or author.get("nickname")
            
            # Build canonical URL
            canonical_url = None
            if creator_handle and external_id:
                canonical_url = f"https://www.tiktok.com/@{creator_handle}/video/{external_id}"
            
            item = NormalizedItem(
                platform="tiktok",
                external_id=external_id,
                content_type="video",
                canonical_url=canonical_url,
                title=None,
                primary_text=aweme.get("desc"),
                published_at=published_at,
                creator_handle=creator_handle,
                metrics=metrics,
                payload={
                    "author": {
                        "uid": author.get("uid"),
                        "unique_id": author.get("unique_id"),
                        "nickname": author.get("nickname"),
                        "avatar": author.get("avatar_thumb", {}).get("url_list", [None])[0],
                    },
                    "music": aweme.get("music", {}),
                    "video_duration": video_obj.get("duration"),
                },
                media_urls=media_urls,
            )
            items.append(item)
        
        # Extract response metadata
        response_meta = {
            "credits_remaining": response_json.get("credits_remaining"),
            "has_more": data.get("has_more"),
        }
        
        # Extract cursor
        next_cursor = None
        cursor = data.get("cursor")
        if cursor is not None:
            next_cursor = {"cursor": cursor}
        
        return ParsedPlatformResponse(
            items=items,
            next_cursor=next_cursor,
            response_meta=response_meta,
            raw_response=response_json,
        )


tiktok_keyword_adapter = TikTokKeywordAdapter()
