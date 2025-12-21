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

from app.auth import get_current_user
from app.core import get_settings, logger
from app.db import get_db_connection, set_rls_user, get_or_create_user, queries
from app.services.user_cache import get_cached_user_uuid
from app.schemas.chats import (
    Chat, 
    CreateChatRequest, 
    SendMessageRequest, 
    Message, 
    ChatHistory
)

router = APIRouter()
settings = get_settings()

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
                "board_id": (context or {}).get("board_id"),
            }
        }
        
        async for ev in graph.astream_events(inputs, config=config, version="v2"):
            ev_type = ev.get("event")
            data = ev.get("data", {}) or {}
            
            payload = None
            
            if ev_type == "on_chain_start":
                # ... existing code ...
                pass

            elif ev_type == "on_chat_model_stream":
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
                payload = {
                    "type": "tool_start",
                    "tool": data.get("name"),
                    "input": data.get("input")
                }
                
            elif ev_type == "on_tool_end":
                payload = {
                    "type": "tool_end",
                    "tool": data.get("name")
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
            title=title
        )
        await conn.commit()
        
        return Chat(
            id=chat_id,
            user_id=user_uuid,
            thread_id=thread_id,
            title=title,
            status="idle",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


@router.get("/", response_model=List[Chat])
async def list_chats(
    user: dict = Depends(get_current_user),
):
    """List all chats for the current user."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        return await queries.get_user_chats(conn, user_uuid)


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
    graph = req_obj.app.state.agent_graph
    if not graph:
        raise HTTPException(status_code=503, detail="Agent service unavailable")
    
    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        thread_id = await queries.get_chat_thread_id(conn, chat_id)
        if not thread_id:
            raise HTTPException(status_code=404, detail="Chat not found")
        
    # Trigger Background Task
    inputs = {
        "messages": [{"role": "user", "content": request.message}],
    }
    
    # Runtime context (not persisted) - includes auth token for tools
    context = {
        "x-auth-token": auth_token,
        "board_id": request.board_id,
    }
    
    logger.info(f"[CHAT] Sending to agent with board_id={request.board_id}, auth_token present: {bool(auth_token)}")
    
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

    # Get graph from app state
    graph = request.app.state.agent_graph
    if not graph:
        raise HTTPException(status_code=503, detail="Agent service unavailable")

    try:
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await graph.aget_state(config)
        
        messages = []
        vals = snapshot.values or {}
        for msg in vals.get("messages", []):
            # Handle both dict and object formats
            if hasattr(msg, "type"):
                m_type = msg.type
                content = getattr(msg, "content", "")
                msg_id = getattr(msg, "id", None)
                additional_kwargs = getattr(msg, "additional_kwargs", {})
            else:
                m_type = msg.get("type")
                content = msg.get("content", "")
                msg_id = msg.get("id")
                additional_kwargs = msg.get("additional_kwargs", {})
            
            if m_type in ["human", "ai"]:
               messages.append(Message(
                   id=msg_id,
                   type=m_type,
                   content=content,
                   additional_kwargs=additional_kwargs
               ))
        return ChatHistory(messages=messages)
    except Exception as e:
        logger.error(f"Error fetching state: {e}")
        return ChatHistory(messages=[])
