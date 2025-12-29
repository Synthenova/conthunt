"""Agent graph definition for ContHunt chat assistant.

This module defines the LangGraph workflow that powers the chat interface.
The graph is compiled with a checkpointer at startup for thread-based persistence.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import get_video_analysis
from app.core import get_settings

settings = get_settings()

# Define tools available to the agent
tools = [get_video_analysis]

# Base system prompt
BASE_SYSTEM_PROMPT = """You are a helpful video assistant for the ContHunt platform. 
You act on behalf of the user to help them find, analyze, and manage their saved video content.
You will receive board/search context in the user's message when available.

Tools available:
- `get_video_analysis`: Get deep insights (summary, topics, hashtags) for a specific video using its media_asset_id.

Guidelines:
- **Parallel Analysis**: When analyzing multiple videos (e.g., "analyze all videos in this board"), call `get_video_analysis` in PARALLEL for each video - make multiple simultaneous tool calls in a single response.
- Always be concise and helpful.
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
