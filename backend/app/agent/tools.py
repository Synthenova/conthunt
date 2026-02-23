"""Agent tools for the ContHunt chat assistant.

These tools make authenticated API calls to the backend to fetch
user data like boards, videos, and analysis.
"""
import os
import json
from uuid import UUID
from enum import Enum
from typing import Optional, List, Dict, Any, Annotated, Literal
import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import InjectedState

from app.core import get_settings, logger
from app.agent.model_factory import init_chat_model, init_chat_model_rated
from app.integrations.posthog_client import capture_event_with_error
from app.llm.context import set_llm_context
from datetime import datetime, timezone

from app.agent.deep_research import gcs_store
from app.db import get_db_connection, set_rls_user, queries
from uuid import UUID

settings = get_settings()


def _get_api_base_url() -> str:
    """Get API base URL for internal/external calls."""
    
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}/v1"


async def _get_headers(config: RunnableConfig) -> Dict[str, str]:
    """Extract auth token from config and build headers."""
    auth_token = config.get("configurable", {}).get("x-auth-token")
    return {
        "Authorization": f"Bearer {auth_token}" if auth_token else "",
        "Content-Type": "application/json"
    }


def _get_user_id(config: RunnableConfig) -> str | None:
    return (config.get("configurable", {}) or {}).get("user_id")


def _is_http_429(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return int(exc.response.status_code) == 429
        except Exception:
            return False
    return False


@tool
async def report_step(step: str, config: RunnableConfig) -> str:
    """
    Report a thinking step to the user.
    Call this because the user likes to know what you are doing.
    Strictly less than 5 words. No trailing dots or ellipsis.
    
    Args:
        step: Brief description (e.g., "Analyzing request", "Searching content")
    """
    return "ok"


@tool
async def report_chosen_videos(
    chosen: list[dict],
    criteria_slug: str,
    config: RunnableConfig,
) -> dict:
    """
    Report chosen videos for the frontend to render.

    Each entry in 'chosen' must have:
      - ref: Video reference like 'viral cooking hacks:V3'
      - reason: Why this video was chosen
      - score: Relevance score (1-10)
    """
    chat_id = (config.get("configurable") or {}).get("chat_id")
    criteria_slug = (criteria_slug or "").strip()
    if not criteria_slug:
        return {"error": "criteria_slug is required"}

    from app.agent.deep_research.ref_resolver import resolve_refs_batch

    # Normalize chosen payload
    normalized = []
    refs_to_resolve: list[str] = []
    for row in chosen or []:
        if not isinstance(row, dict):
            continue
        ref = (row.get("ref") or "").strip()
        if not ref:
            continue
        reason = str(row.get("reason") or "").strip()
        score = int(row.get("score") or 0)
        normalized.append({"ref": ref, "reason": reason, "score": score})
        refs_to_resolve.append(ref)

    if not normalized:
        return {"error": "No valid video refs provided"}

    # Resolve refs → media_asset_ids
    resolved = await resolve_refs_batch(str(chat_id), refs_to_resolve)

    # Build list of resolved UUIDs
    chosen_video_ids: list[str] = []
    unresolved_refs: list[str] = []
    for entry in normalized:
        mid = resolved.get(entry["ref"])
        if mid:
            entry["media_asset_id"] = mid
            chosen_video_ids.append(mid)
        else:
            unresolved_refs.append(entry["ref"])

    if unresolved_refs and not chosen_video_ids:
        return {
            "error": "Could not resolve any video refs to media asset IDs.",
            "unresolved_refs": unresolved_refs,
            "hint": "Make sure the ref format is 'search query:VN' and the search exists.",
        }

    # Validate resolved UUIDs
    parsed_ids: list[UUID] = []
    for mid in chosen_video_ids:
        try:
            parsed_ids.append(UUID(str(mid)))
        except Exception:
            pass

    def _safe_slug(s: str) -> str:
        import re
        s = s.lower()
        s = re.sub(r"[^a-z0-9_-]+", "-", s).strip("-")
        return s or "criteria"

    safe_slug = _safe_slug(criteria_slug)

    saved_as = None
    items = []
    if chat_id and parsed_ids:
        # Build grid-ready items for frontend
        user_uuid = (config.get("configurable") or {}).get("user_id")
        if user_uuid:
            try:
                async with get_db_connection() as conn:
                    await set_rls_user(conn, UUID(str(user_uuid)))
                    items = await queries.get_search_result_items_for_media_asset_ids(conn, parsed_ids)
            except Exception:
                items = []

        # Write chosen-vids-<criteria_slug>-NNN.json at root
        prefix = f"chosen-vids-{safe_slug}-"
        existing = await gcs_store.list_paths(str(chat_id), prefix)
        max_n = 0
        for p in existing:
            if "/" in p:
                continue
            if not p.startswith(prefix) or not p.endswith(".json"):
                continue
            try:
                num = int(p[len(prefix):-len(".json")])
            except Exception:
                continue
            max_n = max(max_n, num)
        saved_as = f"{prefix}{max_n + 1:03d}.json"
        await gcs_store.write_json(
            str(chat_id),
            saved_as,
            {
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "criteria_slug": criteria_slug,
                "chosen": normalized,
                "chosen_video_ids": chosen_video_ids,
                "counts": {
                    "chosen_count": len(chosen_video_ids),
                    "unresolved_count": len(unresolved_refs),
                },
            },
        )

        # Tiny dedupe index for agent memory (cheap to read).
        for entry in normalized:
            if not entry.get("media_asset_id"):
                continue
            await gcs_store.append_jsonl(
                str(chat_id),
                "state/chosen_refs.jsonl",
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "ref": entry.get("ref"),
                    "criteria_slug": criteria_slug,
                    "score": int(entry.get("score") or 0),
                },
            )

    return {
        "criteria_slug": criteria_slug,
        "chosen_count": len(chosen_video_ids),
        "unresolved_refs": unresolved_refs,
        "saved_as": saved_as,
        "items": items,
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
    from app.auth.firebase import init_firebase
    from app.services.analysis_service import analysis_service
    from app.db.session import get_db_connection
    from app.db.queries.analysis import get_video_analysis_by_media_asset
    from app.db import set_rls_user
    
    try:
        headers = await _get_headers(config)
        if not headers.get("Authorization"):
            return {"error": "Authentication required. Please provide x-auth-token."}

        configurable = config.get("configurable", {}) if config else {}
        deep_research_enabled = bool((configurable.get("filters") or {}).get("deep_research_enabled"))
        chat_id = configurable.get("chat_id") if deep_research_enabled else None

        # Decode JWT to get user info including db_user_id
        auth_token = configurable.get("x-auth-token")
        db_user_id = None
        user_role = "free"
        
        if auth_token:
            try:
                init_firebase()
                decoded = firebase_auth.verify_id_token(auth_token)                
                user_role = decoded.get("role", "free")
                db_user_id_str = decoded.get("db_user_id")
                if db_user_id_str:
                    db_user_id = UUID(db_user_id_str)
            except Exception:
                logger.exception("[get_video_analysis] token verification failed")
                pass 
        
        # Require db_user_id - users without it need to re-login
        if not db_user_id:
            return {"error": "Session expired. Please log out and log back in."}
        
        media_asset_uuid = UUID(media_asset_id)
        
        # Trigger unified analysis flow (handles priority downloads, race conditions, etc.)
        try:
            logger.info(f"[DEEP_TOOL] trigger_paid_analysis START user={db_user_id} asset={media_asset_uuid}")
            result = await analysis_service.trigger_paid_analysis(
                user_id=db_user_id,
                user_role=user_role,
                media_asset_id=media_asset_uuid,
                context_source="agent_tool",
                record_streak=True,
                chat_id=chat_id,
            )
            logger.info(f"[DEEP_TOOL] trigger_paid_analysis DONE status={result.status} id={result.id}")
            
            # If already completed, return immediately
            if result.status == "completed" and result.analysis:
                # Return dict for tool output
                return {
                    "id": str(result.id),
                    "media_asset_id": str(result.media_asset_id),
                    "status": "completed",
                    "analysis": result.analysis,
                    "error": None,
                    "cached": result.cached,
                }
            
            # Otherwise, wait for completion via Postgres polling when deep research is enabled.
            analysis_id = str(result.id) if result.id else ""
            if not analysis_id:
                return result.model_dump() if hasattr(result, "model_dump") else result.__dict__  # Fallback

            if not chat_id:
                return result

            poll_timeout_s = float(getattr(settings, "DEEP_RESEARCH_ANALYSIS_POLL_TIMEOUT_S", 180.0))
            first_delay_s = float(getattr(settings, "DEEP_RESEARCH_ANALYSIS_POLL_FIRST_DELAY_S", 40.0))
            interval_s = float(getattr(settings, "DEEP_RESEARCH_ANALYSIS_POLL_INTERVAL_S", 5.0))

            loop = asyncio.get_running_loop()
            deadline = loop.time() + max(1.0, poll_timeout_s)

            # First poll is intentionally delayed to avoid hammering the DB while the
            # analysis job is still being queued/downloaded.
            logger.info(f"[DEEP_TOOL] polling SLEEP first_delay={first_delay_s}s asset={media_asset_uuid}")
            await asyncio.sleep(max(0.0, first_delay_s))

            poll_count = 0
            while True:
                poll_count += 1
                async with get_db_connection() as conn:
                    await set_rls_user(conn, db_user_id)
                    analysis = await get_video_analysis_by_media_asset(conn, media_asset_uuid)

                if analysis:
                    status = analysis.get("status", "")
                    if poll_count % 5 == 1:
                        logger.info(f"[DEEP_TOOL] poll #{poll_count} asset={media_asset_uuid} status={status}")

                    if status == "completed" and analysis.get("analysis_result"):
                        logger.info(f"[DEEP_TOOL] COMPLETED asset={media_asset_uuid}")
                        analysis_data = analysis["analysis_result"]
                        analysis_str = analysis_data.get("analysis") if isinstance(analysis_data, dict) else str(analysis_data)
                        return {
                            "id": str(analysis["id"]),
                            "media_asset_id": str(media_asset_uuid),
                            "status": "completed",
                            "analysis": analysis_str,  # Markdown string
                            "error": None,
                            "cached": True,
                        }
                    if status == "failed":
                        logger.error(f"[DEEP_TOOL] FAILED asset={media_asset_uuid} error={analysis.get('error')}")
                        return {
                            "id": str(analysis["id"]),
                            "media_asset_id": str(media_asset_uuid),
                            "status": "failed",
                            "analysis": None,
                            "error": analysis.get("error", "Analysis failed"),
                            "cached": True,
                        }
                else:
                    logger.warning(f"[DEEP_TOOL] poll #{poll_count} asset={media_asset_uuid} NOT FOUND in DB")

                now = loop.time()
                if now >= deadline:
                    logger.error(f"[DEEP_TOOL] TIMEOUT asset={media_asset_uuid} after {poll_timeout_s}s. Returning processing state.")
                    return {
                        "id": str(analysis_id),
                        "media_asset_id": str(media_asset_uuid),
                        "status": "processing",
                        "analysis": None,
                        "error": None,
                        "message": "Analysis is still processing. Please try again in a moment.",
                        "cached": False,
                    }
                # Fixed cadence after the first delayed poll.
                jitter = 0.05 * ((media_asset_uuid.int >> 64) % 7)
                await asyncio.sleep(max(0.0, interval_s) + jitter)
            
        except Exception as limit_err:
            logger.exception(f"[DEEP_TOOL] Exception in polling loop: {limit_err}")
            return {"error": f"Polling Error: {str(limit_err)}"}

    except ValueError:
        return {"error": "Invalid media_asset_id format."}
    except Exception as e:
        # Catch explicit 402 or "Credit limit exceeded" in error message
        error_str = str(e)
        if "402" in error_str or "Credit limit exceeded" in error_str:
            return {"error": "CREDIT_LIMIT_EXCEEDED: You have run out of credits. Please upgrade your plan to continue."}
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

class TikTokSortBy(str, Enum):
    relevance = "relevance"
    most_liked = "most-liked"
    date_posted = "date-posted"


class TikTokDateFilter(str, Enum):
    this_week = "this-week"
    yesterday = "yesterday"
    this_month = "this-month"
    last_3_months = "last-3-months"
    last_6_months = "last-6-months"
    all_time = "all-time"


class TikTokTopFilters(BaseModel):
    publish_time: Optional[TikTokDateFilter] = None
    sort_by: Optional[TikTokSortBy] = None


class TikTokKeywordFilters(BaseModel):
    date_posted: Optional[TikTokDateFilter] = None
    sort_by: Optional[TikTokSortBy] = None


class SearchFilters(BaseModel):
    tiktok_top: Optional[TikTokTopFilters] = None
    tiktok_keyword: Optional[TikTokKeywordFilters] = None


class SearchPlan(BaseModel):
    queries: List[SearchQuery] = Field(description="List of search queries to execute")
    filters: Optional[SearchFilters] = None


def _llm_filters_to_inputs(filters: SearchFilters) -> dict:
    inputs: Dict[str, Dict[str, Any]] = {}
    if filters.tiktok_top:
        inputs["tiktok_top"] = filters.tiktok_top.model_dump(exclude_none=True, mode="json")
    if filters.tiktok_keyword:
        inputs["tiktok_keyword"] = filters.tiktok_keyword.model_dump(exclude_none=True, mode="json")
    return inputs


def _merge_filter_inputs(base: dict, override: dict) -> dict:
    merged: Dict[str, Dict[str, Any]] = {}
    base = base or {}
    override = override or {}
    for platform in set(base.keys()) | set(override.keys()):
        merged[platform] = {
            **(base.get(platform) or {}),
            **(override.get(platform) or {}),
        }
    return merged




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
        
        # 1. Initialize search-planning model
        llm = init_chat_model("openrouter/google/gemini-3-flash-preview:online")
        structured_llm = llm.with_structured_output(SearchPlan)

        # 2. Extract messages for context
        messages = state.get("messages", [])
        config_filters = configurable.get("filters") or {}
        
        # 3. Generate keywords
        system_msg = SystemMessage(content="""
IMPORTANT OVERRIDE: Not every user message is “inspiration.” First decide if the user intent is DIRECT LOOKUP vs INSPIRATION.

You are an expert search keyword generator specialized in discovering inspirational short-form videos across any niche or topic (e.g., marketing, fitness, cooking, fashion, tech, beauty, education, comedy, travel).
Keyword must not have platform specific keywords (e.g., tiktok, youtube, instagram, etc.)
Note: These keyword combinations will be used in a downstream LLM system that has direct web search access. Optimize them to perform strongly in web searches, surfacing native short-form video results effectively.

A) DIRECT LOOKUP (return 1-2 queries only)
Use DIRECT LOOKUP when the user input is mainly a named entity or specific target, with no “ideas/inspo/examples/hooks” wording.
Examples: show/movie/song/person/brand + qualifiers like season/episode/year/part/version.
- Output: EXACTLY 1-2 keyword combinations (the tightest literal phrase).
- Do NOT create 5 near-duplicates (no padding with “edits”, “scenes”, “reaction” unless the user asks for those).


B) INSPIRATION / DISCOVERY (return 3–5 queries, usually 5)
Use INSPIRATION when the user input is seeking ideas, examples, inspiration, or viral content.
- 2 hyper-niche: Extremely focused on the highest-signal, most authentic/viral elements from the request (e.g., raw relatable moments or peak format matches).
- 3 niche: Highly accurate and specific, capturing core themes with slight variations.
Step-by-step thinking for INSPIRATION / DISCOVERY (do this internally before outputting):
1. Decompose the user's request: Identify main themes (e.g., viral style, humor, tutorials, challenges, creative ideas), desired formats (POV, skit, reaction, day-in-the-life, hook, fail, transformation), and any sub-aspects (authenticity, low-budget, relatable struggles, surprises).
2. Infer common short-form video patterns for the niche: Use creator-style phrases that appear in real video titles (e.g., "POV ...", "day I tried ...", "funny ... fail", "before after ...", "trying viral ...").
3. Keep combinations short and compound (3-8 words max). Focus purely on descriptive core keywords.
4. Hashtags: Include only if they naturally boost relevance in the niche (e.g., popular trend tags); never force them.
5. Prioritize phrases that surface native, authentic videos via web search: Avoid anything that pulls articles, lists, or compilations (no "best", "top", "examples", "ideas list").
6. Diversify across the request's key angles (e.g., humor, virality, tutorials, relatability) while staying tightly on-topic.

C) Use web_search if needed to understand the topic better.

D) If the user explicitly requests filters (date, sort), include them in `filters`.
Allowed values:
- publish_time/date_posted: this-week, yesterday, this-month, last-3-months, last-6-months, all-time
- sort_by: relevance, most-liked, date-posted
        """)
        
        # Combine history into one human message
        history_parts = []
        for msg in messages:
            content_str = ""
            if msg.type == "human":
                content_str = str(msg.content)
                prefix = "User: "
            elif msg.type == "ai":
                if isinstance(msg.content, list):
                    parts = []
                    for block in msg.content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            parts.append(block)
                    content_str = "\n".join(parts)
                else:
                    content_str = str(msg.content)
                prefix = "AI: "
            
            if content_str and content_str.strip():
                history_parts.append(f"{prefix}{content_str.strip()}")
        
        combined_content = "\n".join(history_parts)        
        # Invoke the model
        try:
           # We pass the conversation history + system prompt
           with set_llm_context(user_id=_get_user_id(config), route="search.plan"):
               response = await structured_llm.ainvoke([system_msg, HumanMessage(content=combined_content)])
        except Exception as llm_err:
             capture_event_with_error(
                 distinct_id=_get_user_id(config) or "system:search_plan",
                 event="search_plan_failed",
                 exception=llm_err,
                 properties={
                     "route": "search.plan",
                     "is_429": _is_http_429(llm_err),
                 },
             )
             return {"error": f"Failed to generate search keywords: {str(llm_err)}"}

        if not response or not response.queries:
             return {"error": "Could not generate valid search queries."}

        queries = response.queries
        llm_filters = response.filters
        llm_filter_inputs = _llm_filters_to_inputs(llm_filters) if llm_filters else {}
        effective_filters = _merge_filter_inputs(config_filters, llm_filter_inputs)
        platforms_list = AVAILABLE_PLATFORMS
        logger.info(f"Generated search queries: {queries}")
        logger.info(f"Generated filters: {llm_filters}")
        logger.info(f"Config filters: {config_filters}")
        logger.info(f"Effective filters: {effective_filters}")
        logger.info(f"Platforms list: {platforms_list}")

        search_ids = []
        errors = []
        results_info = []

        import asyncio

        async def _execute_single_search(query_item, sort_order_val):
            keyword = query_item.keyword
            
            if not keyword:
                return None

            # Always search all available platforms unless explicitly limited by LLM platforms
            resolved_platforms = platforms_list
            inputs = {
                platform: dict(effective_filters.get(platform, {}))
                for platform in resolved_platforms
            }
            logger.info(f"Executing search using inputs: {inputs}")
            
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
            except httpx.HTTPStatusError as e:
                # Explicitly handle 402 Credit Limit errors
                if e.response.status_code == 402:
                    return {"error": "CREDIT_LIMIT_EXCEEDED: You have run out of credits. Please upgrade your plan to continue."}
                return {"error": f"Failed to start search for '{keyword}': {str(e)}"}
            except Exception as e:
                # Handle cases where backend error detail contains info
                if "Credit limit exceeded" in str(e):
                    return {"error": "CREDIT_LIMIT_EXCEEDED: You have run out of credits. Please upgrade your plan to continue."}
                return {"error": f"Failed to start search for '{keyword}': {str(e)}"}
            return None

        # Execute parallel searches (cap configurable)
        tasks = []
        max_searches = max(1, int(getattr(settings, "SEARCH_ENQUEUE_BATCH_SIZE", 5)))
        # sort_order: -1, -2, -3...
        for idx, q in enumerate(queries[:max_searches]):
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
            "message": f"I have started {len(search_ids)} searches for you: {', '.join([q['keyword'] for q in results_info])}. Do NOT fetch results in this turn.",
            "errors": errors if errors else None
        }
    except Exception as e:
        return {"error": f"Search tool error: {str(e)}"}


@tool
async def get_search_items(
    search_id: str,
    config: RunnableConfig,
) -> str | Dict[str, Any]:
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

            lines = []
            lines.append(f"Search: {search_data.get('query')}")
            lines.append(f"Count: {len(items)}")
            lines.append("")
            for idx, item in enumerate(items, start=1):
                title = (item.get("title") or "Untitled").strip()
                creator = (item.get("creator_handle") or "unknown").strip()
                caption = (item.get("primary_text") or "").strip()
                published_at = item.get("published_at") or "unknown"
                media_asset_id = item.get("media_asset_id") or "n/a"
                metrics = item.get("metrics") or {}
                metric_names = ", ".join(sorted(metrics.keys())) if metrics else "n/a"
                lines.append(f"{idx}.")
                lines.append(f"{title}")
                lines.append(f"{creator}")
                if caption:
                    lines.append(f"caption: {caption}")
                lines.append(f"posted_at: {published_at}")
                lines.append(f"media_asset_id: {media_asset_id}")
                lines.append(f"metrics: {metric_names}")
                lines.append("")

            return "\n".join(lines).strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Search not found: {search_id}"}
        return {"error": f"Failed to get search items: {e.response.text}"}
    except Exception as e:
        return {"error": f"Error fetching search items: {str(e)}"}
