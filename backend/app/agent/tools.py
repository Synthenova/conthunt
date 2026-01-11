"""Agent tools for the ContHunt chat assistant.

These tools make authenticated API calls to the backend to fetch
user data like boards, videos, and analysis.
"""
import os
from uuid import UUID
from typing import Optional, List, Dict, Any, Annotated
import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import InjectedState

from app.core import get_settings
from app.agent.model_factory import init_chat_model

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
    Call this because the user likes to know what you are doing.
    
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
async def search_my_videos(
    query: str,
    config: RunnableConfig,
    board_id: Optional[str] = None,
    search_options: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search the user's OWN indexed video library for specific moments.
    
    USE THIS TOOL when the user wants to search within videos they have ALREADY saved to their boards.
    This uses TwelveLabs AI to search across visual content, audio, and transcription.
    
    DO NOT use this for finding NEW content - use the `search` tool instead for discovering 
    new videos from TikTok, Instagram, YouTube, etc.
    
    Args:
        query: What to search for (e.g., "someone cooking pasta", "talking about AI").
        board_id: Optional. Limit search to videos in a specific board.
                  If not provided, searches ALL user's indexed videos across all boards.
        search_options: Types of content to search: ["visual", "audio", "transcription"].
                       Default is all three.
    
    Returns:
        Search results with video clips, timestamps, thumbnails, and relevance ranking.
    """
    try:
        from app.core import logger
        from app.db.session import get_db_connection
        from app.db.queries.twelvelabs import resolve_indexed_asset_ids_to_media
        
        logger.info(f"[search_my_videos] INPUT: query={query!r}, board_id={board_id}, search_options={search_options}")
        
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
            result = response.json()
        
        # Resolve TwelveLabs video_ids to media details
        raw_clips = result.get("data", [])
        if not raw_clips:
            return {"clips": [], "count": 0}
        
        # Get unique video_ids (TwelveLabs indexed_asset_ids)
        video_ids = list(set(clip["video_id"] for clip in raw_clips))
        
        # Resolve to media details
        async with get_db_connection() as conn:
            id_mapping = await resolve_indexed_asset_ids_to_media(conn, video_ids)
        
        # Build clean response
        clips = []
        for clip in raw_clips:
            video_id = clip["video_id"]
            media_info = id_mapping.get(video_id, {})
            
            clips.append({
                "media_asset_id": media_info.get("media_asset_id"),
                "title": media_info.get("title"),
                "platform": media_info.get("platform"),
                "start": clip.get("start"),
                "end": clip.get("end"),
                "confidence": clip.get("confidence"),
            })
        
        logger.info(f"[search_my_videos] OUTPUT: {len(clips)} clips resolved")
        return {"clips": clips, "count": len(clips)}
        
    except httpx.HTTPStatusError as e:
        from app.core import logger
        logger.error(f"[search_my_videos] HTTP ERROR: {e.response.text}")
        return {"error": f"Search failed: {e.response.text}"}
    except Exception as e:
        from app.core import logger
        logger.error(f"[search_my_videos] ERROR: {str(e)}")
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
    import asyncio
    from firebase_admin import auth as firebase_auth
    from app.services.analysis_service import analysis_service
    from app.db.session import get_db_connection
    from app.db.queries.analysis import get_video_analysis_by_media_asset
    from app.schemas.analysis import VideoAnalysisResult
    
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        # Decode JWT to get user info including db_user_id
        auth_token = config.get("configurable", {}).get("x-auth-token")
        db_user_id = None
        user_role = "free"
        
        if auth_token:
            try:
                decoded = firebase_auth.verify_id_token(auth_token)
                user_role = decoded.get("role", "free")
                db_user_id_str = decoded.get("db_user_id")
                if db_user_id_str:
                    db_user_id = UUID(db_user_id_str)
            except Exception:
                pass 
        
        # Require db_user_id - users without it need to re-login
        if not db_user_id:
            return {"error": "Session expired. Please log out and log back in."}
        
        media_asset_uuid = UUID(media_asset_id)
        
        # Trigger unified analysis flow (handles priority downloads, race conditions, etc.)
        try:
            result = await analysis_service.trigger_paid_analysis(
                user_id=db_user_id,
                user_role=user_role,
                media_asset_id=media_asset_uuid,
                context_source="agent_tool"
            )
            
            # Convert to dict if needed
            if hasattr(result, 'model_dump'):
                result = result.model_dump()
            
            # If already completed, return immediately
            if result.get("status") == "completed" and result.get("analysis"):
                return result
            
            # Otherwise, poll for completion (max 60 seconds)
            # Since we prioritized the upload, it should complete quickly
            analysis_id = result.get("id")
            if not analysis_id:
                return result  # Can't poll without ID
            
            for attempt in range(12):  # 12 x 5s = 60 seconds
                await asyncio.sleep(5)
                
                async with get_db_connection() as conn:
                    analysis = await get_video_analysis_by_media_asset(conn, media_asset_uuid)
                
                if not analysis:
                    continue
                    
                status = analysis.get("status", "")
                
                if status == "completed" and analysis.get("analysis_result"):
                    return {
                        "id": str(analysis["id"]),
                        "media_asset_id": str(media_asset_uuid),
                        "status": "completed",
                        "analysis": analysis["analysis_result"],
                        "error": None,
                        "cached": True,
                    }
                elif status == "failed":
                    return {
                        "id": str(analysis["id"]),
                        "media_asset_id": str(media_asset_uuid),
                        "status": "failed",
                        "analysis": None,
                        "error": analysis.get("error", "Analysis failed"),
                        "cached": True,
                    }
                # Still processing, continue polling
            
            # Timeout - return processing status
            return {
                "id": str(analysis_id),
                "media_asset_id": str(media_asset_uuid),
                "status": "processing",
                "analysis": None,
                "error": None,
                "message": "Analysis is still processing. The video may still be uploading. Please try again in a moment.",
                "cached": False,
            }
            
        except Exception as limit_err:
            return {"error": str(limit_err)}

    except ValueError:
        return {"error": "Invalid media_asset_id format."}
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}


# Available platform slugs for search
AVAILABLE_PLATFORMS = ["tiktok_top", "tiktok_keyword", "instagram_reels", "youtube"]


@tool
async def get_chat_searches(
    chat_id: str,
    config: RunnableConfig,
) -> Dict[str, Any]:
    """
    Get search tags linked to a chat.
    
    Args:
        chat_id: Chat UUID.
    
    Returns:
        Dict with searches (id, label, sort_order).
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        url = f"{_get_api_base_url()}/chats/{chat_id}/tags"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            tags = resp.json()
            searches = [
                {"id": t.get("id"), "label": t.get("label"), "sort_order": t.get("sort_order")}
                for t in tags
                if t.get("type") == "search"
            ]
            return {"chat_id": chat_id, "searches": searches, "count": len(searches)}
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to fetch chat searches: {e.response.text}"}
    except Exception as e:
        return {"error": f"Error fetching chat searches: {str(e)}"}


class SearchQuery(BaseModel):
    keyword: str = Field(description="The search keyword")

class SearchKeywords(BaseModel):
    queries: List[SearchQuery] = Field(description="List of search queries to execute")


@tool
async def search(
    state: Annotated[dict, InjectedState],
    config: RunnableConfig,
) -> Dict[str, Any]:
    """
    Trigger content searches based on the current conversation context.
    
    Call this tool when the user expresses a desire to find content, videos, or inspiration.
    You do NOT need to provide arguments; this tool will analyze the conversation history
    to generate the best search queries automatically.
    """
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        configurable = config.get("configurable", {}) if config else {}
        chat_id = configurable.get("chat_id")
        
        
        # 1. Initialize Gemini 3 Pro for intent detection
        llm = init_chat_model("google/gemini-3-pro-preview")
        structured_llm = llm.with_structured_output(SearchKeywords)

        # 2. Extract messages for context
        messages = state.get("messages", [])
        
        # 3. Generate keywords
        system_msg = SystemMessage(content="""
        You are a search expert. Analyze the conversation history and user request to understand their intent.
        Generate 3 to 5 distinct, high-quality search queries that will help the user find what they are looking for.
        For each query, provide ONLY the keyword.
        Focus on finding content related to the user's request.
        """)
        
        # Invoke the model
        try:
           # We pass the conversation history + system prompt
           response = await structured_llm.ainvoke([system_msg] + messages)
        except Exception as llm_err:
             return {"error": f"Failed to generate search keywords: {str(llm_err)}"}

        if not response or not response.queries:
             return {"error": "Could not generate valid search queries."}

        queries = response.queries
        search_ids = []
        errors = []
        results_info = []

        import asyncio

        async def _execute_single_search(query_item, sort_order_val):
            keyword = query_item.keyword
            
            if not keyword:
                return None

            # Always search all available platforms
            platforms_list = AVAILABLE_PLATFORMS
            inputs = {platform: {} for platform in platforms_list}
            
            url = f"{_get_api_base_url()}/search"
            payload = {
                "query": keyword,
                "inputs": inputs
            }
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    result = resp.json()
                    s_id = result.get("search_id")
                    
                    if s_id:
                        # Tag it
                        if chat_id:
                            try:
                                tag_url = f"{_get_api_base_url()}/chats/{chat_id}/tags"
                                tag_payload = {
                                    "tags": [{
                                        "type": "search",
                                        "id": s_id,
                                        "label": keyword,
                                        "source": "agent",
                                        "sort_order": sort_order_val,
                                    }]
                                }
                                await client.post(tag_url, headers=headers, json=tag_payload)
                            except Exception as tag_err:
                                return {"error": f"Tagged search but failed to save to chat: {tag_err}"}
                        
                        return {
                            "search_id": s_id,
                            "keyword": keyword,
                            "platforms": list(inputs.keys())
                        }
            except Exception as e:
                return {"error": f"Failed to start search for '{keyword}': {str(e)}"}
            return None

        # Execute parallel searches
        tasks = []
        # sort_order: -1, -2, -3...
        for idx, q in enumerate(queries):
            tasks.append(_execute_single_search(q, -(idx + 1)))
        
        results = await asyncio.gather(*tasks)

        for res in results:
            if not res:
                continue
            if "error" in res:
                errors.append(res["error"])
            elif "search_id" in res:
                search_ids.append(res["search_id"])
                results_info.append(res)
        
        if not search_ids and errors:
            return {"error": "; ".join(errors)}
        
        return {
            "search_ids": search_ids,
            "generated_queries": results_info,
            "message": f"I have started {len(search_ids)} searches for you: {', '.join([q['keyword'] for q in results_info])}. Use get_search_items(search_id) to retrieve results once complete. Please report strictly the started searches to the user.",
            "errors": errors if errors else None
        }
    except Exception as e:
        return {"error": f"Search tool error: {str(e)}"}


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
