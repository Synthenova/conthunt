"""Agent tools for the ContHunt chat assistant.

These tools make authenticated API calls to the backend to fetch
user data like boards, videos, and analysis.
"""
import os
from uuid import UUID
from typing import Optional, List, Dict, Any
import httpx
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.core import get_settings
from app.agent.analysis_inline import run_inline_video_analysis

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
async def report_step(step: str, config: RunnableConfig) -> str:
    """
    Report a thinking step to the user.
    Call this before each major action to explain what you're about to do.
    
    Args:
        step: Brief description of current step (e.g., "Analyzing your request", "Searching for content")
    """
    return "ok"


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

        return await run_inline_video_analysis(UUID(media_asset_id))
    except ValueError:
        return {"error": "Invalid media_asset_id format."}
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}


# Available platform slugs for search
AVAILABLE_PLATFORMS = ["tiktok_top", "tiktok_keyword", "instagram_reels", "youtube"]


@tool
async def search(
    queries: List[Dict[str, Any]],
    config: RunnableConfig,
) -> Dict[str, Any]:
    """
    Trigger content searches across platforms. Returns search IDs immediately.
    Searches run asynchronously - use get_search_items() later to retrieve results.
    
    Args:
        queries: List of search queries. Each query is a dict with:
            - keyword (str): The search term (e.g., "compressible sofas")
            - platforms (List[str]): Platform slugs to search. If empty, uses all platforms.
              Available: tiktok_top, tiktok_keyword, instagram_reels, youtube
    
    Returns:
        Dict with 'search_ids' list and instructions for next steps.
    
    Example:
        search([
            {"keyword": "compressible sofas", "platforms": []},
            {"keyword": "vacuum furniture", "platforms": ["tiktok_keyword"]}
        ])
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        configurable = config.get("configurable", {}) if config else {}
        chat_id = configurable.get("chat_id")

        search_ids = []
        errors = []
        
        for query in queries:
            keyword = query.get("keyword", "")
            platforms = query.get("platforms", [])
            
            if not keyword:
                continue
            
            # If no platforms specified, use all available
            if not platforms:
                platforms = AVAILABLE_PLATFORMS
            
            # Build inputs dict for each platform
            inputs = {platform: {} for platform in platforms if platform in AVAILABLE_PLATFORMS}
            
            if not inputs:
                errors.append(f"No valid platforms for '{keyword}'")
                continue
            
            # POST /v1/search
            url = f"{_get_api_base_url()}/search"
            payload = {
                "query": keyword,
                "inputs": inputs
            }
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    search_id = result.get("search_id")
                    if search_id:
                        search_ids.append({
                            "search_id": search_id,
                            "keyword": keyword,
                            "platforms": list(inputs.keys())
                        })
                        if chat_id:
                            try:
                                tag_url = f"{_get_api_base_url()}/chats/{chat_id}/tags"
                                tag_payload = {
                                    "tags": [{
                                        "type": "search",
                                        "id": search_id,
                                        "label": keyword,
                                        "source": "agent",
                                    }]
                                }
                                await client.post(tag_url, headers=headers, json=tag_payload)
                            except Exception as tag_err:
                                errors.append(f"Tagged search but failed to save to chat: {tag_err}")
            except Exception as e:
                errors.append(f"Failed to start search for '{keyword}': {str(e)}")
        
        if not search_ids and errors:
            return {"error": "; ".join(errors)}
        
        return {
            "search_ids": search_ids,
            "message": f"Started {len(search_ids)} search(es). Use get_search_items(search_id) to retrieve results once complete. If results aren't ready yet, inform the user and try again next turn.",
            "errors": errors if errors else None
        }
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}


@tool
async def get_search_items(
    search_id: str,
    config: RunnableConfig,
) -> Dict[str, Any]:
    """
    Get video results from a completed search.
    
    Args:
        search_id: The search ID returned by the search() tool.
    
    Returns:
        List of videos with title, platform, creator_handle, content_type, primary_text, media_asset_id.
        Returns error if search is still running or not found.
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        # First check if search is complete
        url = f"{_get_api_base_url()}/searches/{search_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            search_data = response.json()
            
            status = search_data.get("status")
            if status == "running":
                return {
                    "status": "running",
                    "message": "Search is still running. Please wait and try again in the next turn."
                }
            elif status == "failed":
                return {
                    "status": "failed",
                    "message": "Search failed. You may want to try a new search."
                }
            
            # Search is complete - get items summary
            summary_url = f"{_get_api_base_url()}/searches/{search_id}/items/summary"
            summary_response = await client.get(summary_url, headers=headers)
            summary_response.raise_for_status()
            items = summary_response.json()
            
            return {
                "status": "completed",
                "query": search_data.get("query"),
                "items": items,
                "count": len(items)
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Search not found: {search_id}"}
        return {"error": f"Failed to get search items: {e.response.text}"}
    except Exception as e:
        return {"error": f"Error fetching search items: {str(e)}"}
