import asyncio
import json
import uuid
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
from langgraph_sdk import get_client

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
    chat_id: str,
    thread_id: str,
    inputs: dict,
    context: dict | None = None,
):
    """
    Background task:
    1. Stream from LangGraph.
    2. Filter Assistant deltas.
    3. Push to Redis Stream `chat:{id}:stream`.
    4. Cleanup Redis key on finish.
    """
    logger.info(f"Starting background stream for chat {chat_id}")
    
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    lg_client = get_client(url=settings.LANGGRAPH_URL)
    stream_key = f"chat:{chat_id}:stream"

    try:
        config_obj = {"configurable": context} if context else None        
        async for event in lg_client.runs.stream(
            thread_id=thread_id,
            assistant_id="agent",
            input=inputs,
            stream_mode="events",
            config=config_obj,
        ):
            # logger.info(f"Stream Event: {str(event)[:500]}")
            # Log already added previously
            if event.event == "events" and event.data:
                print(f"[DEBUG] Stream Event Data: {json.dumps(event.data, default=str)}") # Added log for inspection
            # The SDK returns StreamPart(event='events', data={'event': 'on_chat_model_stream', ...})
            if event.event == "events" and event.data:
                inner_event = event.data
                ev_type = inner_event.get("event")
                data = inner_event.get("data", {})
                
                payload = None
                
                if ev_type == "on_chain_start":
                    # Try to capture the Human Message ID from the input
                    try:
                        inp = data.get("input", {})
                        if isinstance(inp, dict):
                            msgs = inp.get("messages", [])
                            if msgs and isinstance(msgs, list):
                                first_msg = msgs[0]
                                if isinstance(first_msg, dict) and first_msg.get("type") == "human":
                                    human_id = first_msg.get("id")
                                    if human_id:
                                        payload = {
                                            "type": "user_message_id",
                                            "id": human_id
                                        }
                    except Exception as e:
                        logger.warning(f"Error extracting human message ID: {e}")

                elif ev_type == "on_chat_model_stream":
                    chunk = data.get("chunk", {})
                    content = chunk.get("content", "")
                    msg_id = chunk.get("id")
                    if content:
                        payload = {
                            "type": "content_delta",
                            "content": content,
                            "id": msg_id
                        }
                        
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
                    await r.xadd(stream_key, {"data": json.dumps(payload)})

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
    
    # 1. Create LangGraph thread
    lg_client = get_client(url=settings.LANGGRAPH_URL)
    try:
        thread = await lg_client.threads.create()
    except Exception as e:
        logger.error(f"Failed to create LangGraph thread: {e}")
        raise HTTPException(status_code=503, detail="Chat service unavailable")

    # 2. Insert into DB
    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        chat_id = uuid.uuid4()
        title = request.title or "New Chat"
        
        await queries.create_chat(
            conn=conn,
            chat_id=chat_id,
            user_id=user_uuid,
            thread_id=thread["thread_id"],
            title=title
        )
        await conn.commit()
        
        return Chat(
            id=chat_id,
            user_id=user_uuid,
            thread_id=thread["thread_id"],
            title=title,
            status="idle",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    return Chat(...) # Logic helper for typing if needed, but return above covers it

from datetime import datetime

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
    req_obj: Request, # Need Request object to get headers
    user: dict = Depends(get_current_user),
):
    """Send a message (triggers background stream)."""
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    # Extract auth token from header
    auth_header = req_obj.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
         # Should ideally not happen if get_current_user passed, but specific token needed
         # In Firebase auth, the token is reused. 
         # get_current_user verifies it but doesn't return the raw token string usually?
         # Depends on implementation. We grab it from header to be safe.
         raise HTTPException(status_code=401, detail="Missing Bearer token")
    
    auth_token = auth_header.split(" ")[1]

    
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
    
    # Runtime context (not in state) - includes auth token for tools
    context = {
        "x-auth-token": auth_token,  # Tools read this for API calls
        "board_id": request.board_id,
    }
    
    print(f"[CHAT] Sending to agent with board_id={request.board_id}, auth_token present: {bool(auth_token)}")
    
    background_tasks.add_task(
        stream_generator_to_redis,
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
    user: dict = Depends(get_current_user),
):
    """Get confirmed history from LangGraph."""
    user_id = user.get("uid")
    if not user_id:
         raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, user_id)
        await set_rls_user(conn, user_uuid)
        
        thread_id = await queries.get_chat_thread_id(conn, chat_id)
        if not thread_id:
            raise HTTPException(status_code=404, detail="Chat not found")

    lg_client = get_client(url=settings.LANGGRAPH_URL)
    try:
        current_state = await lg_client.threads.get_state(thread_id)
        messages = []
        if "messages" in current_state["values"]:
            for msg in current_state["values"]["messages"]:
                m_type = msg.get("type")
                if m_type in ["human", "ai"]:
                   messages.append(Message(
                       id=msg.get("id"),
                       type=m_type,
                       content=msg.get("content", ""),
                       additional_kwargs=msg.get("additional_kwargs", {})
                   ))
        return ChatHistory(messages=messages)
    except Exception as e:
        logger.error(f"Error fetching state: {e}")
        return ChatHistory(messages=[])
