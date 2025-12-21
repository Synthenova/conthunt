"""Agent tools for the ContHunt chat assistant.

These tools make authenticated API calls to the backend to fetch
user data like boards, videos, and analysis.
"""
import os
from typing import Optional, List, Dict, Any
import httpx
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.core import get_settings

settings = get_settings()


def _get_api_base_url() -> str:
    """Get API base URL - use localhost with correct port for internal calls."""
    # Cloud Run sets PORT env var; default to 8000 for local dev
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}/v1"


async def _get_headers(config: RunnableConfig) -> Dict[str, str]:
    """Extract auth token from config and build headers."""
    auth_token = config.get("configurable", {}).get("x-auth-token")
    return {
        "Authorization": f"Bearer {auth_token}" if auth_token else "",
        "Content-Type": "application/json"
    }


@tool
async def get_user_boards(config: RunnableConfig) -> List[Dict[str, Any]]:
    """
    Fetch a list of all boards created by the user. 
    Returns a list of dictionaries with 'id' and 'name' of the boards.
    Use this to see what boards the user has organized their videos into.
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return [{"error": "Authentication required. Please provide x-auth-token."}]

        url = f"{_get_api_base_url()}/boards/"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return [{"error": f"Failed to fetch boards: {e.response.text}"}]
    except Exception as e:
        return [{"error": f"Error fetching boards: {str(e)}"}]


@tool
async def get_board_items(
    board_id: str,
    config: RunnableConfig,
) -> List[Dict[str, Any]]:
    """
    Fetch all video items within a specific board.
    Returns a simplified list with: 'title', 'platform', 'creator_handle', 'content_type', 'primary_text', 'media_asset_id'.
    Use 'media_asset_id' for search_12labs filtering or video analysis.
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return [{"error": "Authentication required. Please provide x-auth-token."}]

        url = f"{_get_api_base_url()}/boards/{board_id}/items/summary"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return [{"error": f"Failed to fetch board items: {e.response.text}"}]
    except Exception as e:
        return [{"error": f"Error fetching board items: {str(e)}"}]


@tool
async def search_videos(
    query: str,
    config: RunnableConfig,
    board_id: Optional[str] = None,
    search_options: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search for specific moments across the user's indexed videos.
    
    This searches across visual content, audio, and transcription 
    to find clips matching your query.
    
    Args:
        query: What to search for (e.g., "someone cooking pasta", "talking about AI").
        board_id: Optional. Limit search to videos in a specific board.
                  If not provided, searches all user's videos across all boards.
        search_options: Types of content to search: ["visual", "audio", "transcription"].
                       Default is all three.
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        url = f"{_get_api_base_url()}/twelvelabs/search"
        payload = {
            "query": query,
            "search_options": search_options if search_options else ["visual", "audio", "transcription"]
        }
        if board_id:
            payload["board_id"] = board_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Search failed: {e.response.text}"}
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}


@tool
async def get_video_analysis(
    media_asset_id: str,
    config: RunnableConfig,
) -> Dict[str, Any]:
    """
    Retrieve detailed AI analysis for a specific video (identified by media_asset_id).
    This includes summary, key topics, and hashtags.
    Use this when the user asks for "analysis" or "summary" of a specific video they found.
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        url = f"{_get_api_base_url()}/video-analysis/{media_asset_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to get analysis: {e.response.text}"}
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}
