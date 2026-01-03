"""Chat API endpoints - POST /v1/chats with Redis streaming.

Uses direct LangGraph graph calls instead of the LangGraph SDK,
with AsyncPostgresSaver for thread-based persistence.
"""
import asyncio
import json
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
from pydantic import BaseModel
try:
    from psycopg.errors import OperationalError
except Exception:  # pragma: no cover - fallback if psycopg isn't available
    OperationalError = Exception

from app.auth import get_current_user
from app.core import get_settings, logger
from app.db import get_db_connection, set_rls_user, get_or_create_user, queries
from app.services.user_cache import get_cached_user_uuid
from app.agent.runtime import create_agent_graph
from app.schemas.chats import (
    Chat, 
    CreateChatRequest, 
    SendMessageRequest, 
    Message, 
    ChatHistory,
    RenameChatRequest,
    ChatTag,
)

router = APIRouter()
settings = get_settings()

class UpsertChatTagsRequest(BaseModel):
    tags: List[ChatTag]

class UpdateTagOrdersRequest(BaseModel):
    orders: List[dict]

# --- Dependencies ---

async def get_redis():
    """Get Redis client instance."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


# --- Background Task Logic ---

async def stream_generator_to_redis(
    graph,  # The compiled graph from app.state
    chat_id: str,
    thread_id: str,
    inputs: dict,
    context: dict | None = None,
):
    """
    Background task:
    1. Stream from LangGraph using direct graph.astream_events().
    2. Filter Assistant deltas.
    3. Push to Redis Stream `chat:{id}:stream`.
    4. Cleanup Redis key on finish.
    """
    logger.info(f"Starting background stream for chat {chat_id}")
    
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    stream_key = f"chat:{chat_id}:stream"

    try:
        # Build config with thread_id for persistence and context for tools
        config = {
            "configurable": {
                "thread_id": thread_id,
                "x-auth-token": (context or {}).get("x-auth-token"),
                "chat_id": chat_id,
            }
        }
        tool_run_ids = set()
        
        async for ev in graph.astream_events(inputs, config=config, version="v2"):
            ev_type = ev.get("event")
            data = ev.get("data", {}) or {}
            run_id = ev.get("run_id")
            parent_run_id = ev.get("parent_run_id")
            metadata = ev.get("metadata") or {}
            langgraph_node = metadata.get("langgraph_node")
            
            payload = None
            
            if ev_type == "on_chain_start":
                # ... existing code ...
                pass

            elif ev_type == "on_chat_model_stream":
                # Only forward assistant model streams, not tool-internal LLM runs.
                if parent_run_id in tool_run_ids:
                    logger.debug(
                        "[CHAT] Skipping nested model stream from tool run_id=%s parent_run_id=%s name=%s node=%s",
                        run_id,
                        parent_run_id,
                        ev.get("name"),
                        langgraph_node,
                    )
                    continue
                if langgraph_node and langgraph_node != "agent":
                    logger.debug(
                        "[CHAT] Skipping model stream for non-agent node run_id=%s parent_run_id=%s name=%s node=%s",
                        run_id,
                        parent_run_id,
                        ev.get("name"),
                        langgraph_node,
                    )
                    continue
                chunk = data.get("chunk")
                if chunk:
                    # chunk might be an AIMessageChunk object
                    content = getattr(chunk, "content", "") if hasattr(chunk, "content") else chunk.get("content", "")
                    msg_id = getattr(chunk, "id", None) if hasattr(chunk, "id") else chunk.get("id")
                    
                    if content:
                        payload = {
                            "type": "content_delta",
                            "content": content,
                            "id": msg_id
                        }
                    else:
                        # Sometimes empty chunks come through e.g. at start/end
                        pass
                        
            elif ev_type == "on_tool_start":
                if run_id:
                    tool_run_ids.add(run_id)
                logger.debug(
                    "[CHAT] Tool start name=%s run_id=%s parent_run_id=%s node=%s",
                    ev.get("name"),
                    run_id,
                    parent_run_id,
                    langgraph_node,
                )
                payload = {
                    "type": "tool_start",
                    "tool": ev.get("name"),
                    "run_id": run_id,
                    "input": data.get("input")
                }
                
            elif ev_type == "on_tool_end":
                if run_id and run_id in tool_run_ids:
                    tool_run_ids.discard(run_id)
                tool_output = data.get("output")
                # If output is a Message object (like ToolMessage), extract content
                if hasattr(tool_output, "content"):
                    final_output = tool_output.content
                else:
                    final_output = tool_output
                    
                payload = {
                    "type": "tool_end",
                    "tool": ev.get("name"),
                    "run_id": run_id,
                    "output": final_output
                }

            if payload:
                await r.xadd(stream_key, {"data": json.dumps(payload, default=str)})

        await r.xadd(stream_key, {"data": json.dumps({"type": "done"})})

    except Exception as e:
        logger.error(f"Background stream error for {chat_id}: {e}", exc_info=True)
        await r.xadd(stream_key, {"data": json.dumps({"type": "error", "error": str(e)})})
        
    finally:
        await r.expire(stream_key, 60)
        await r.close()
        logger.info(f"Background stream finished for {chat_id}")


# --- Endpoints ---


async def _refresh_agent_graph(request: Request):
    """Recreate the LangGraph instance and its saver when the connection drops."""
    saver_cm = getattr(request.app.state, "_agent_saver_cm", None)
    if saver_cm:
        try:
            await saver_cm.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing previous agent saver: {e}")

    graph, saver_cm = await create_agent_graph(settings.DATABASE_URL)
    request.app.state.agent_graph = graph
    request.app.state._agent_saver_cm = saver_cm
    return graph


async def _get_agent_graph(request: Request):
    """Return the cached graph, refreshing if connection is stale."""
    graph = getattr(request.app.state, "agent_graph", None)
    if not graph:
        return await _refresh_agent_graph(request)
    
    # Proactively test the checkpointer connection before using it
    try:
        # Quick health check - try to get state for a non-existent thread
        # This will fail fast if connection is closed
        await graph.aget_state({"configurable": {"thread_id": "__health_check__"}})
    except OperationalError:
        logger.warning("Agent graph connection stale, refreshing before use")
        return await _refresh_agent_graph(request)
    except Exception:
        # Other errors (e.g., thread not found) are fine - connection is alive
        pass
    
    return graph

@router.post("", response_model=Chat)
@router.post("/", response_model=Chat)
async def create_chat(
    request: CreateChatRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new chat session."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Thread ID is just a UUID - the checkpointer uses it as the key
    thread_id = str(uuid.uuid4())

    # Insert into DB
    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        chat_id = uuid.uuid4()
        title = request.title or "New Chat"
        
        await queries.create_chat(
            conn=conn,
            chat_id=chat_id,
            user_id=user_uuid,
            thread_id=thread_id,
            title=title,
            context_type=request.context_type,
            context_id=request.context_id,
        )
        await conn.commit()
        
        return Chat(
            id=chat_id,
            user_id=user_uuid,
            thread_id=thread_id,
            title=title,
            context_type=request.context_type,
            context_id=request.context_id,
            status="idle",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


@router.get("", response_model=List[Chat])
@router.get("/", response_model=List[Chat])
async def list_chats(
    user: dict = Depends(get_current_user),
    context_type: Optional[str] = None,
    context_id: Optional[uuid.UUID] = None,
):
    """List all chats for the current user."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        return await queries.get_user_chats(
            conn,
            user_uuid,
            context_type=context_type,
            context_id=context_id,
        )


@router.post("/{chat_id}/tags")
async def upsert_tags(
    chat_id: uuid.UUID,
    request: UpsertChatTagsRequest,
    user: dict = Depends(get_current_user),
):
    """Attach tags to a chat (boards/searches/media)."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)

        exists = await queries.check_chat_exists(conn, chat_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Chat not found")

        tags = [
            {
                "type": tag.type,
                "tag_id": tag.id,
                "label": tag.label,
                "source": tag.source or "user",
                "sort_order": tag.sort_order,
            }
            for tag in (request.tags or [])
        ]
        await queries.upsert_chat_tags(conn, chat_id, tags)
        await conn.commit()

    return {"ok": True, "count": len(request.tags or [])}


@router.get("/{chat_id}/tags", response_model=List[ChatTag])
async def list_tags(
    chat_id: uuid.UUID,
    user: dict = Depends(get_current_user),
):
    """Fetch tags for a chat."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)

        exists = await queries.check_chat_exists(conn, chat_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Chat not found")

        tags = await queries.get_chat_tags(conn, chat_id)

    return [
        ChatTag(
            type=t["type"],
            id=t["tag_id"],
            label=t.get("label"),
            source=t.get("source") or "user",
            sort_order=t.get("sort_order"),
            created_at=t.get("created_at"),
        )
        for t in tags
    ]


@router.patch("/{chat_id}/tags/order")
async def update_tag_order(
    chat_id: uuid.UUID,
    request: UpdateTagOrdersRequest,
    user: dict = Depends(get_current_user),
):
    """Update sort_order for tags in a chat."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)

        exists = await queries.check_chat_exists(conn, chat_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Chat not found")

        await queries.update_chat_tag_orders(conn, chat_id, request.orders or [])
        await conn.commit()

    return {"ok": True}


@router.post("/{chat_id}/send")
async def send_message(
    chat_id: uuid.UUID,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    req_obj: Request,
    user: dict = Depends(get_current_user),
):
    """Send a message (triggers background stream)."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    # Extract auth token from header
    auth_header = req_obj.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Missing Bearer token")
    
    auth_token = auth_header.split(" ")[1]

    # Get graph from app state
    graph = await _get_agent_graph(req_obj)
    
    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        thread_id = await queries.get_chat_thread_id(conn, chat_id)
        if not thread_id:
            raise HTTPException(status_code=404, detail="Chat not found")

        if request.tags:
            tags = [
                {
                    "type": tag.type,
                    "tag_id": tag.id,
                    "label": tag.label,
                    "source": tag.source or "user",
                }
                for tag in request.tags
            ]
            await queries.upsert_chat_tags(conn, chat_id, tags)
            await conn.commit()
        
    # Trigger Background Task
    user_message: dict = {"role": "user", "content": request.message}
    if request.client_id:
        user_message["additional_kwargs"] = {"client_id": request.client_id}

    inputs = {
        "messages": [user_message],
    }
    
    # Runtime context (not persisted) - includes auth token for tools
    context = {
        "x-auth-token": auth_token,
    }
    
    logger.info(f"[CHAT] Sending to agent, auth_token present: {bool(auth_token)}")

    # Clear previous stream data to prevent replaying old messages within 60s window
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await r.delete(f"chat:{str(chat_id)}:stream")
    finally:
        await r.close()
    
    background_tasks.add_task(
        stream_generator_to_redis,
        graph=graph,
        chat_id=str(chat_id),
        thread_id=thread_id,
        inputs=inputs,
        context=context,
    )
    
    return {"ok": True}


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: uuid.UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a chat session."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        exists = await queries.check_chat_exists(conn, chat_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        await queries.delete_chat(conn, chat_id)
        await conn.commit()
        
    return {"ok": True}


@router.patch("/{chat_id}/title", response_model=Chat)
async def rename_chat(
    chat_id: uuid.UUID,
    request: RenameChatRequest,
    user: dict = Depends(get_current_user),
):
    """Rename a chat session."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)

        chat = await queries.update_chat_title(conn, chat_id, request.title)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        await conn.commit()

    return chat


@router.get("/{chat_id}/stream")
async def stream_chat(
    chat_id: uuid.UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    redis_client: redis.Redis = Depends(get_redis),
):
    """SSE endpoint for chat updates."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        exists = await queries.check_chat_exists(conn, chat_id)
        if not exists:
             raise HTTPException(status_code=404, detail="Chat not found")

    stream_key = f"chat:{str(chat_id)}:stream"

    async def event_generator():
        last_id = last_event_id or "0-0"
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                    
                streams = await redis_client.xread(
                    {stream_key: last_id}, 
                    count=50, 
                    block=10000 
                )
                
                if not streams:
                    yield {"event": "ping", "data": ""}
                    continue
                    
                for _, messages in streams:
                    for msg_id, data_map in messages:
                        last_id = msg_id
                        payload_str = data_map.get("data")
                        yield {
                            "id": msg_id,
                            "event": "message",
                            "data": payload_str
                        }
                        
                        # Check if done to close stream
                        if payload_str and '"type": "done"' in payload_str:
                             return
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator())


@router.get("/{chat_id}/messages", response_model=ChatHistory)
async def get_chat_messages(
    chat_id: uuid.UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Get confirmed history from the checkpointer."""
    user_id = user.get("uid")
    if not user_id:
         raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        thread_id = await queries.get_chat_thread_id(conn, chat_id)
        if not thread_id:
            raise HTTPException(status_code=404, detail="Chat not found")

    # Get graph from app state (refresh if missing)
    graph = await _get_agent_graph(request)

    try:
        config = {"configurable": {"thread_id": thread_id}}
        try:
            snapshot = await graph.aget_state(config)
        except OperationalError as e:
            logger.warning(f"Agent graph connection lost, refreshing and retrying: {e}")
            graph = await _refresh_agent_graph(request)
            snapshot = await graph.aget_state(config)
        
        messages = []
        vals = snapshot.values or {}
        for msg in vals.get("messages", []):
            # Handle both dict and object formats
            if hasattr(msg, "type"):
                m_type = msg.type
                content = getattr(msg, "content", "")
                msg_id = getattr(msg, "id", None)
                tool_calls = getattr(msg, "tool_calls", [])
                additional_kwargs = getattr(msg, "additional_kwargs", {})
            else:
                m_type = msg.get("type")
                content = msg.get("content", "")
                msg_id = msg.get("id")
                tool_calls = msg.get("tool_calls", [])
                additional_kwargs = msg.get("additional_kwargs", {})
            
            if m_type in ["human", "ai", "tool"]:
               messages.append(Message(
                   id=msg_id,
                   type=m_type,
                   content=content,
                   tool_calls=tool_calls,
                   additional_kwargs=additional_kwargs
               ))

        return ChatHistory(messages=messages)
    except Exception as e:
        logger.error(f"Error fetching state: {e}")
        return ChatHistory(messages=[])
