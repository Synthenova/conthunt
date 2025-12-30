"""Agent graph definition for ContHunt chat assistant.

This module defines the LangGraph workflow that powers the chat interface.
The graph is compiled with a checkpointer at startup for thread-based persistence.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import (
    get_video_analysis,
    get_board_items,
    get_search_items,
    search,
)
from app.core import get_settings

settings = get_settings()

# Define tools available to the agent
tools = [get_video_analysis, get_board_items, get_search_items, search]

# Base system prompt
BASE_SYSTEM_PROMPT = """You are a helpful content assistant for the ContHunt platform.
You help users find, analyze, and manage video content across multiple platforms.

Tools available:
- `search(queries)`: Trigger searches for content. Takes list of {{keyword, platforms}}. Returns search IDs.
- `get_search_items(search_id)`: Get video results from a completed search.
- `get_board_items(board_id)`: Get videos from a user's board.
- `get_video_analysis(media_asset_id)`: Get AI analysis (summary, topics, hashtags) for a video.

Guidelines:

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
    
    # Create the LLM with tools
    # Using Vertex AI via ChatGoogleGenerativeAI to match analysis.py pattern
    # Native support without creating a separate ChatVertexAI instance if this works well
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0.5,
        project=settings.GCLOUD_PROJECT,
        vertexai=True,
    )
    model = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | model
    response = await chain.ainvoke({"messages": messages}, config=config)
    return {"messages": [response]}


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
