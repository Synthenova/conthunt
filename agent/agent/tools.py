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
    Returns a list of items with details like 'title', 'id', 'content_type'.
    """
    try:
        config = get_config()
        auth_token = config.get("configurable", {}).get("x-auth-token")
        if not auth_token:
            return [{"error": "Authentication required. Please provide x-auth-token."}]

        url = f"{API_BASE_URL}/boards/{board_id}/items"
        headers = await _get_headers(auth_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return [{"error": f"Failed to fetch board items: {e.response.text}"}]
    except Exception as e:
        return [{"error": f"Error fetching board items: {str(e)}"}]

@tool
async def search_12labs(
    query: str,    
    search_options: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search for video clips across the user's indexed videos using 12Labs semantic search.
    Use this when the user asks a broad question or wants to find specific moments in videos.
    
    Args:
        query: The search query string.
        search_options: Optional types of data to search. Allowed: ["visual", "audio", "transcription"].
                       Default is all three. Use specifics if user asks e.g. "show me X" (visual) vs "who said Y" (transcription).
    """
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Search failed: {e.response.text}"}
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}

@tool
async def get_video_analysis(
    content_item_id: str,
) -> Dict[str, Any]:
    """
    Retrieve detailed AI analysis for a specific video (identified by content_item_id).
    This includes summary, key topics, and hashtags.
    Use this when the user asks for "analysis" or "summary" of a specific video they found.
    """
    try:
        config = get_config()
        auth_token = config.get("configurable", {}).get("x-auth-token")
        if not auth_token:
            return {"error": "Authentication required. Please provide x-auth-token."}

        url = f"{API_BASE_URL}/video-analysis/{content_item_id}"
        headers = await _get_headers(auth_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to get analysis: {e.response.text}"}
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}
