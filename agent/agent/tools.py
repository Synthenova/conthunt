from typing import Optional, List, Dict, Any
import os
import httpx
from langchain_core.tools import tool
from langgraph.config import get_config

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/v1")

async def _get_headers(auth_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

@tool
async def get_user_boards() -> List[Dict[str, Any]]:
    """
    Fetch a list of all boards created by the user. 
    Returns a list of dictionaries with 'id' and 'name' of the boards.
    Use this to see what boards the user has organized their videos into.
    """
    try:
        config = get_config()
        auth_token = config.get("configurable", {}).get("x-auth-token")
        print("GOMMALE",auth_token)
        if not auth_token:
            return [{"error": "Authentication required. Please provide x-auth-token."}]

        url = f"{API_BASE_URL}/boards/"
        headers = await _get_headers(auth_token)
        
        async with httpx.AsyncClient() as client:
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
) -> List[Dict[str, Any]]:
    """
    Fetch all video items within a specific board.
    Returns a simplified list with: 'title', 'platform', 'creator_handle', 'content_type', 'primary_text', 'media_asset_id'.
    Use 'media_asset_id' for search_12labs filtering or video analysis.
    """
    print(f"[AGENT TOOL] get_board_items called with board_id={board_id}")
    try:
        config = get_config()
        auth_token = config.get("configurable", {}).get("x-auth-token")
        print(f"[AGENT TOOL] auth_token present: {bool(auth_token)}")
        if not auth_token:
            return [{"error": "Authentication required. Please provide x-auth-token."}]

        url = f"{API_BASE_URL}/boards/{board_id}/items/summary"
        print(f"[AGENT TOOL] Calling URL: {url}")
        headers = await _get_headers(auth_token)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            print(f"[AGENT TOOL] Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"[AGENT TOOL] Response items count: {len(result) if isinstance(result, list) else 'not a list'}")
            return result
    except httpx.HTTPStatusError as e:
        print(f"[AGENT TOOL] HTTP error: {e.response.status_code} - {e.response.text}")
        return [{"error": f"Failed to fetch board items: {e.response.text}"}]
    except Exception as e:
        print(f"[AGENT TOOL] Exception: {type(e).__name__}: {e}")
        return [{"error": f"Error fetching board items: {str(e)}"}]

@tool
async def search_videos(
    query: str,    
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
    print(f"[AGENT TOOL] search_videos called: query='{query}', board_id={board_id}")
    try:
        config = get_config()
        auth_token = config.get("configurable", {}).get("x-auth-token")
        if not auth_token:
            return {"error": "Authentication required. Please provide x-auth-token."}

        url = f"{API_BASE_URL}/twelvelabs/search"
        headers = await _get_headers(auth_token)
        payload = {
            "query": query,
            "search_options": search_options if search_options else ["visual", "audio", "transcription"]
        }
        if board_id:
            payload["board_id"] = board_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"[AGENT TOOL] search_videos response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"[AGENT TOOL] search_videos HTTP error: {e.response.text}")
        return {"error": f"Search failed: {e.response.text}"}
    except Exception as e:
        print(f"[AGENT TOOL] search_videos exception: {e}")
        return {"error": f"Search error: {str(e)}"}

@tool
async def get_video_analysis(
    media_asset_id: str,
) -> Dict[str, Any]:
    """
    Retrieve detailed AI analysis for a specific video (identified by media_asset_id).
    This includes summary, key topics, and hashtags.
    Use this when the user asks for "analysis" or "summary" of a specific video they found.
    """
    try:
        config = get_config()
        auth_token = config.get("configurable", {}).get("x-auth-token")
        if not auth_token:
            return {"error": "Authentication required. Please provide x-auth-token."}

        url = f"{API_BASE_URL}/video-analysis/{media_asset_id}"
        headers = await _get_headers(auth_token)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to get analysis: {e.response.text}"}
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}
