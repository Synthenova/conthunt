"""Agent graph definition for ContHunt chat assistant.

This module defines the LangGraph workflow that powers the chat interface.
The graph is compiled with a checkpointer at startup for thread-based persistence.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.model_factory import (
    get_model_provider,
    init_chat_model,
    normalize_messages_for_provider,
)
from app.agent.tools import (
    get_video_analysis,
    get_board_items,
    get_search_items,
    search,
    report_step,
    get_chat_searches,
)
# Define tools available to the agent
tools = [report_step, get_video_analysis, get_board_items, get_search_items, search, get_chat_searches]

# Base system prompt
BASE_SYSTEM_PROMPT = """You are a helpful content assistant for the ContHunt platform.
You help users find, analyze, and manage video content across multiple platforms.

Tools available:
- `report_step(step)`: Report what you're doing to the user. Call before major actions.
- `search(queries)`: Trigger searches for content. Takes list of {{keyword, platforms}}. Returns search IDs.
- `get_search_items(search_id)`: Get video results from a completed search.
- `get_board_items(board_id)`: Get videos from a user's board.
- `get_video_analysis(media_asset_id)`: Get AI analysis (summary, topics, hashtags) for a video.

Guidelines:

**Progress Reporting:**
- Always call report_step() before calling search, get_search_items, get_board_items, or get_video_analysis.
- Example: report_step("Searching for ski content and others..") then search(...)

**Searching for Content:**
- When user asks to search/find content, generate relevant keywords and call `search()`.
- If user specifies platforms (e.g., "search TikTok"), use those. Otherwise, search all platforms.
- The search() tool returns search IDs. You must then call `get_search_items()` to get results.
- If get_search_items() says "still running", tell the user to wait and try again next turn.

**Handling @mentions:**
- If user mentions a board with @BoardName, call `get_board_items(board_id)` to get its contents.
- If user mentions a search with @SearchName, call `get_search_items(search_id)` to get its results.

**Video Analysis:**
- When analyzing multiple videos, call `get_video_analysis` in PARALLEL for efficiency.

**General:**
- Be concise and helpful.
- Show search results clearly with titles, platforms, and creators.
"""


async def call_model(state: MessagesState, config: RunnableConfig):
    """Agent node that calls the LLM with tools bound."""
    messages = state["messages"]
    
    system_prompt = BASE_SYSTEM_PROMPT

    model_name = (config.get("configurable") or {}).get("model_name")
    image_urls = set((config.get("configurable") or {}).get("image_urls") or [])
    provider = get_model_provider(model_name)
    if provider == "google":
        messages = _strip_stale_image_blocks(messages, image_urls)
    llm = init_chat_model(model_name, temperature=0.5)
    messages = normalize_messages_for_provider(messages, model_name)
    model = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | model
    response = await chain.ainvoke({"messages": messages}, config=config)
    return {"messages": [response]}


def _strip_stale_image_blocks(messages: list, allowed_urls: set[str]) -> list:
    """Remove image blocks not in the current request to avoid stale signed URLs."""
    if not messages:
        return messages

    def extract_url(block: dict) -> str | None:
        if block.get("type") == "image_url":
            return (block.get("image_url") or {}).get("url")
        if block.get("type") == "image":
            return block.get("url")
        return None

    def update_message_content(message: object, content: object) -> object:
        if isinstance(message, dict):
            updated = dict(message)
            updated["content"] = content
            return updated
        if hasattr(message, "model_copy"):
            return message.model_copy(update={"content": content})
        if hasattr(message, "copy"):
            try:
                return message.copy(update={"content": content})
            except TypeError:
                pass
        try:
            data = dict(message.__dict__)
            data["content"] = content
            return message.__class__(**data)
        except Exception:
            try:
                setattr(message, "content", content)
            except Exception:
                return message
            return message

    updated_messages: list = []
    for msg in messages:
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
        if not isinstance(content, list):
            updated_messages.append(msg)
            continue

        filtered = []
        for block in content:
            if isinstance(block, dict) and block.get("type") in ("image", "image_url"):
                url = extract_url(block)
                if url and url in allowed_urls:
                    filtered.append(block)
                continue
            filtered.append(block)

        if filtered == content:
            updated_messages.append(msg)
        else:
            updated_messages.append(update_message_content(msg, filtered if filtered else ""))

    return updated_messages


def build_graph(checkpointer):
    """
    Build and compile the agent graph with the given checkpointer.
    
    Args:
        checkpointer: A LangGraph checkpointer (e.g., AsyncPostgresSaver)
                     for persisting conversation state across messages.
    
    Returns:
        Compiled graph ready for invoke/stream operations.
    """
    workflow = StateGraph(MessagesState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")
    
    # Compile with checkpointer for persistence
    return workflow.compile(checkpointer=checkpointer)
