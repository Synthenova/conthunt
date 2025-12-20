from typing import Literal, Annotated
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from agent.tools import get_user_boards, get_board_items, search_12labs, get_video_analysis

load_dotenv()

# Define AgentState
class AgentState(MessagesState):
    pass

# Define tools
tools = [get_user_boards, get_board_items, search_12labs, get_video_analysis]

# Define the model
llm = ChatOpenAI(
    model="google/gemini-2.5-flash", 
    temperature=0.5, 
    api_key=os.getenv("OPENAI_API_KEY")
)
model = llm.bind_tools(tools)

# Define system prompt
SYSTEM_PROMPT = """You are a helpful video assistant for the ContHunt platform. 
You act on behalf of the user to help them find, analyze, and manage their saved video content.
You have access to their boards and can perform semantic searches across their videos using 12Labs.

Tools available:
- `get_user_boards`: See what boards the user has.
- `get_board_items`: See videos in a board.
- `search_12labs`: Search for specific moments, objects, or concepts in their videos.
- `get_video_analysis`: Get deep insights (summary, topics) for a specific video.

Guidelines:
- If the user asks general questions like "what do I have?", start by checking their boards to get context.
- If the user asks about a specific topic (e.g., "find clips of cats"), use `search_12labs`.
- If the user asks about a specific video they see or mentioned, use `get_video_analysis`.
- Always be concise and helpful.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])

# Define the node
async def call_model(state: AgentState):
    messages = state["messages"]
    chain = prompt | model
    response = await chain.ainvoke(messages)
    return {"messages": [response]}

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Add edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# Compile
graph = workflow.compile()
