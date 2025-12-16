"""TwelveLabs API client wrapper for video analysis."""
import asyncio
import logging
from typing import Optional

from twelvelabs import TwelveLabs

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

# Default analysis prompt for extracting content insights
DEFAULT_ANALYSIS_PROMPT = """Analyze this video and extract the following information:
1. Hook: The attention-grabbing opening (first 3 seconds)
2. Call to Action: Any requests for viewer engagement (subscribe, like, follow, etc.)
3. On-screen texts: Any text overlays or captions shown in the video
4. Key topics: Main subjects or themes discussed
5. Summary: A brief 2-3 sentence summary of the video content
6. Hashtags: Suggested hashtags for this content

Be specific and extract actual content from the video, not generic descriptions."""

# JSON schema for structured response
ANALYSIS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {
            "type": "string",
            "description": "The attention-grabbing opening hook of the video"
        },
        "call_to_action": {
            "type": "string",
            "description": "Any call to action present in the video"
        },
        "on_screen_texts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of text overlays shown in the video"
        },
        "key_topics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Main topics or themes in the video"
        },
        "summary": {
            "type": "string",
            "description": "Brief summary of the video content"
        },
        "hashtags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Suggested hashtags for the video"
        }
    },
    "required": ["hook", "summary"]
}


class TwelvelabsClient:
    """Wrapper around TwelveLabs SDK for video analysis."""
    
    def __init__(self):
        settings = get_settings()
        if not settings.TWELVELABS_API_KEY:
            raise ValueError("TWELVELABS_API_KEY is not set")
        self.client = TwelveLabs(api_key=settings.TWELVELABS_API_KEY)
        self.settings = settings
    
    async def upload_asset(self, video_url: str) -> tuple[str, dict]:
        """
        Upload a video to TwelveLabs via URL.
        
        Returns (asset_id, raw_response_dict).
        """
        logger.info(f"Uploading video to TwelveLabs: {video_url[:100]}...")
        
        # The SDK is synchronous, run in executor
        loop = asyncio.get_event_loop()
        asset = await loop.run_in_executor(
            None,
            lambda: self.client.assets.create(
                method="url",
                url=video_url,
            )
        )
        
        logger.info(f"Asset created: {asset.id}, status: {asset.status}")
        
        # Capture raw response for archiving
        raw_response = {
            "id": asset.id,
            "method": str(asset.method) if asset.method else None,
            "status": str(asset.status) if asset.status else None,
            "filename": asset.filename,
            "file_type": asset.file_type,
            "url": asset.url,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
        }
        return asset.id, raw_response
    
    async def wait_for_asset_ready(
        self, 
        asset_id: str, 
        timeout: Optional[int] = None
    ) -> bool:
        """
        Poll until asset upload is ready.
        
        Returns True if ready, False if failed or timeout.
        """
        timeout = timeout or self.settings.TWELVELABS_UPLOAD_TIMEOUT
        poll_interval = 5  # seconds
        elapsed = 0
        
        loop = asyncio.get_event_loop()
        
        while elapsed < timeout:
            asset = await loop.run_in_executor(
                None,
                lambda: self.client.assets.retrieve(asset_id)
            )
            
            logger.debug(f"Asset {asset_id} status: {asset.status}")
            
            if asset.status == "ready":
                return True
            elif asset.status == "failed":
                logger.error(f"Asset upload failed: {asset_id}")
                return False
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        logger.error(f"Asset upload timeout after {timeout}s: {asset_id}")
        return False
    
    async def get_or_create_index(self, index_name: str) -> str:
        """
        [DEPRECATED] Get existing index by name or create new one.
        We now use a single static index configured via env vars.
        Keeping this method temporarily to avoid immediate import errors if called elsewhere,
        but it should return the env var ID if possible or be removed.
        """
        if self.settings.TWELVELABS_INDEX_ID:
            return self.settings.TWELVELABS_INDEX_ID
        
        # Fallback to old logic or error out
        logger.warning("get_or_create_index called but TWELVELABS_INDEX_ID is set. Returning configured ID.")
        return self.settings.TWELVELABS_INDEX_ID

    
    async def index_asset(self, index_id: str, asset_id: str) -> tuple[str, dict]:
        """
        Index an asset into a 12Labs index.
        
        Returns (indexed_asset_id, raw_response_dict).
        """
        logger.info(f"Indexing asset {asset_id} into index {index_id}")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.indexes.indexed_assets.create(
                index_id=index_id,
                asset_id=asset_id,
                enable_video_stream=False,
            )
        )
        
        logger.info(f"Indexed asset ID: {result.id}")
        
        # Capture raw response for archiving
        raw_response = {
            "id": result.id,
            "index_id": index_id,
            "asset_id": asset_id,
        }
        
        return result.id, raw_response
    
    async def wait_for_indexing_ready(
        self,
        index_id: str,
        indexed_asset_id: str,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Poll until asset indexing is ready.
        
        Returns True if ready, False if failed or timeout.
        """
        timeout = timeout or self.settings.TWELVELABS_INDEX_TIMEOUT
        poll_interval = 5  # seconds
        elapsed = 0
        
        loop = asyncio.get_event_loop()
        
        while elapsed < timeout:
            asset = await loop.run_in_executor(
                None,
                lambda: self.client.indexes.indexed_assets.retrieve(
                    index_id=index_id,
                    indexed_asset_id=indexed_asset_id,
                )
            )
            
            logger.debug(f"Indexed asset {indexed_asset_id} status: {asset.status}")
            
            if asset.status == "ready":
                return True
            elif asset.status == "failed":
                logger.error(f"Asset indexing failed: {indexed_asset_id}")
                return False
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        logger.error(f"Asset indexing timeout after {timeout}s: {indexed_asset_id}")
        return False
    
    async def analyze_video(
        self,
        indexed_asset_id: str,
        prompt: Optional[str] = None,
    ) -> dict:
        """
        Analyze a video and get structured insights.
        
        Returns dict with: analysis, token_usage, generation_id, raw_response.
        """
        prompt = prompt or DEFAULT_ANALYSIS_PROMPT
        
        logger.info(f"Analyzing video: {indexed_asset_id}")
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                lambda: self.client.analyze(
                    video_id=indexed_asset_id,
                    prompt=prompt,
                    temperature=0.2,
                    response_format={
                        "type": "json_schema",
                        "json_schema": ANALYSIS_RESPONSE_SCHEMA
                    },
                    max_tokens=2000,
                )
            )
            
            # Parse the response data (it's a JSON string)
            import json
            if result.data:
                try:
                    analysis = json.loads(result.data)
                except json.JSONDecodeError:
                    analysis = {"summary": result.data, "raw_text": result.data}
            else:
                analysis = {"summary": "No analysis data returned"}
            
            token_usage = result.usage.output_tokens if result.usage else None
            
            logger.info(f"Analysis complete. Tokens used: {token_usage}")
            
            # Capture full raw response for archiving
            raw_response = {
                "id": result.id,
                "data": result.data,
                "finish_reason": str(result.finish_reason) if result.finish_reason else None,
                "usage": {
                    "output_tokens": result.usage.output_tokens
                } if result.usage else None,
            }
            
            return {
                "analysis": analysis,
                "token_usage": token_usage,
                "generation_id": result.id,
                "raw_response": raw_response,
            }
            
        except Exception as e:
            logger.error(f"TwelveLabs API error: {e}")
            raise


# Singleton instance
_client: Optional[TwelvelabsClient] = None


def get_twelvelabs_client() -> TwelvelabsClient:
    """Get or create the TwelveLabs client singleton."""
    global _client
    if _client is None:
        _client = TwelvelabsClient()
    return _client
