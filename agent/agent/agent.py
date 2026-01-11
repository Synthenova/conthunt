from typing import Optional
from dataclasses import dataclass
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime
from langgraph.checkpoint.postgres import PostgresSaver

from agent.tools import get_user_boards, get_board_items, search_videos, get_video_analysis

load_dotenv()

# Define Runtime Context Schema
@dataclass
class ContextSchema:
    board_id: Optional[str] = None  # Current board context

# Define tools
tools = [get_user_boards, get_board_items, get_video_analysis]#, search_videos]

# Define checkpointer
postgres_url = os.getenv("POSTGRES_URL")
checkpointer = PostgresSaver.from_conn_string(postgres_url)
with PostgresSaver.from_conn_string(postgres_url) as checkpointer:
    # call .setup() the first time you're using the checkpointer
    checkpointer.setup()
    


# Define the model
llm = ChatOpenAI(
    model="google/gemini-3-flash", 
    temperature=0.5, 
    api_key=os.getenv("OPENAI_API_KEY")
)
model = llm.bind_tools(tools)

# Define base system prompt
BASE_SYSTEM_PROMPT = """You are a helpful video assistant for the ContHunt platform. 
You act on behalf of the user to help them find, analyze, and manage their saved video content.
You have access to their boards and can perform semantic searches across their videos.

Tools available:
- `get_user_boards`: See what boards the user has.
- `get_board_items`: See videos in a board. Returns a list of videos with their media_asset_id.
- `get_video_analysis`: Get deep insights (summary, topics, hashtags) for a specific video using its media_asset_id.

Guidelines:
- If the user asks general questions like "what do I have?", start by checking their boards to get context.
- If the user asks about a specific topic (e.g., "find clips of cats"), use `search_videos`.
- If the user wants to search within a specific board, use `search_videos` with the board_id.
- **Parallel Analysis**: When analyzing multiple videos (e.g., "analyze all videos in this board"), call `get_video_analysis` in PARALLEL for each video - make multiple simultaneous tool calls in a single response.
- Always be concise and helpful.
"""

# Define the node with runtime context
async def call_model(state: MessagesState, runtime: Runtime[ContextSchema]):
    messages = state["messages"]
    board_id = runtime.context.board_id
    
    # Build system prompt with optional board context
    system_prompt = BASE_SYSTEM_PROMPT
    if board_id:
        system_prompt += f"\n\n**Current Context**: The user is viewing board ID: {board_id}. When they ask about 'this board' or 'these videos', use this board_id."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | model
    response = await chain.ainvoke({"messages": messages})
    return {"messages": [response]}

# Define the graph with context schema
workflow = StateGraph(MessagesState, context_schema=ContextSchema)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Add edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# Compile
graph = workflow.compile(checkpointer=checkpointer)
