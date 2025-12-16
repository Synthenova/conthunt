# Chat Integration (Backend)

## Overview
Implemented a robust, "backend-only" chat architecture that integrates **LangGraph** with **Redis Streams** for durable, reconnectable streaming. The system allows users to create chat sessions, send messages, and receive streaming responses via Server-Sent Events (SSE) without relying on complex websocket state or persistent worker queues.

## Architecture

1.  **Direct Async Streaming**: 
    - `POST /send` triggers a FastAPI `BackgroundTask`.
    - The background task executes the LangGraph run and pushes events to Redis.
    - This avoids the need for a separate worker/queue infrastructure for simple streaming.

2.  **Persistence**:
    - **Postgres (LangGraph)**: Stores the authoritative state (checkpoints) of the conversation.
    - **Postgres (App)**: `conthunt.chats` maps `chat_id` (App) to `thread_id` (LangGraph).
    - **Redis**: Acts as a temporary, high-speed buffer for live stream chunks.

3.  **Reconnection Strategy**:
    - **Hot Reconnect**: Clients use `Last-Event-ID` to resume a stream from the exact point of disconnection.
    - **History Alignment**: On page load, clients first fetch committed history (`GET /messages`) and then subscribe to the stream (`id=0-0` or last ID) to catch up.

## SQL Schema

### `conthunt.chats`
Stores metadata and mapping for user chat sessions.

```sql
CREATE TABLE conthunt.chats (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES conthunt.users(id) ON DELETE CASCADE,
  thread_id     text NOT NULL UNIQUE, -- Maps to LangGraph thread
  title         text,
  status        text NOT NULL DEFAULT 'idle',
  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now(),
  deleted_at    timestamptz
);
```
*Note: `chat_stream_state` was initially proposed but removed as vestigial in the direct-streaming model.*

## API Endpoints (`/v1/chats`)

### 1. Create Chat
- **POST** `/`
- **Body**: `{"title": "..."}`
- **Logic**: Creates a LangGraph thread, inserts into DB, returns `chat_id`.

### 2. Send Message
- **POST** `/{chat_id}/send`
- **Body**: `{"message": "..."}`
- **Logic**: 
    - Verifies ownership.
    - Triggers `stream_generator_to_redis` in background.
    - Returns `200 OK` immediately.

### 3. Stream (SSE)
- **GET** `/{chat_id}/stream`
- **Headers**: `Last-Event-ID` (optional, auto-sent by browser)
- **Logic**:
    - Uses `Last-Event-ID` (or `0-0` if missing) as the Redis Stream ID.
    - Calls `redis.xread({key: last_id}, block=10000)`.
    - Yields SSE events: `id: <redis_id>`, `event: message`, `data: <json_payload>`.
    - **Auto-Close**: Terminates connection when `{"type": "done"}` is encountered.

### 4. Get History
- **GET** `/{chat_id}/messages`
- **Logic**: Calls `langgraph.threads.get_state` to retrieve specific `Human` and `AI` messages processed by the graph.

## Redis Streaming Logic

**Producer (`chats.py` -> `stream_generator_to_redis`)**
- Consumes `lg_client.runs.stream`.
- Filters specific events: `on_chat_model_stream` (content deltas) and tool events.
- Wraps them in JSON and pushes to `xadd`.
- Pushes `done` marker at the end.
- **Cleanup**: Sets `expire` on the stream key (60s) after completion to prevent stale data.

**Consumer (Frontend/Client)**
- Connects to SSE.
- If disconnected, reconnects with `Last-Event-ID`.
- Backend replays missed events from Redis buffer.
