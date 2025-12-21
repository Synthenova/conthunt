
import asyncio
import os
import uuid
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, MessagesState
from app.agent.graph import build_graph
from app.core import get_settings

# Mock settings just to get DB URL
settings = get_settings()

async def inspect_history(chat_thread_id: str):
    print(f"Inspecting history for thread: {chat_thread_id}")
    
    # Setup checkpointer
    # Use the same connection string logic as runtime.py
    from urllib.parse import quote
    pg_url = settings.DATABASE_URL
    if pg_url.startswith("postgresql+psycopg://"):
        pg_url = pg_url.replace("postgresql+psycopg://", "postgresql://")
    
    schema = settings.DB_SCHEMA
    options_param = quote(f"-c search_path={schema},public")
    if "?" in pg_url:
        pg_url = f"{pg_url}&options={options_param}"
    else:
        pg_url = f"{pg_url}?options={options_param}"

    async with AsyncPostgresSaver.from_conn_string(pg_url) as checkpointer:
        # We don't need the graph to just read state, but let's build it to be safe
        graph = build_graph(checkpointer)
        
        config = {"configurable": {"thread_id": chat_thread_id}}
        state = await graph.aget_state(config)
        
        if not state.values:
            print("No state found!")
            return

        messages = state.values.get("messages", [])
        print(f"Found {len(messages)} messages:")
        
        ids = []
        for m in messages:
            m_id = getattr(m, "id", "NO_ID")
            m_type = getattr(m, "type", "NO_TYPE")
            content = getattr(m, "content", "")[:50]
            print(f"ID: {m_id} | Type: {m_type} | Content: {content}...")
            ids.append(m_id)
            
        # Check duplicates
        if len(ids) != len(set(ids)):
            print("\n!!! DUPLICATE IDS FOUND !!!")
            from collections import Counter
            counts = Counter(ids)
            for i, c in counts.items():
                if c > 1:
                    print(f"Duplicate ID: {i} (Count: {c})")
        else:
            print("\nNo duplicate IDs found in backend history.")

if __name__ == "__main__":
    # USER provided thread ID
    thread_id = "29ca5d4a-3d73-4239-bfe9-2ef4559620a5"
    asyncio.run(inspect_history(thread_id))
