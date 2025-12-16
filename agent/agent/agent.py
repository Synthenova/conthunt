from typing import Literal
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, MessagesState

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "your-project-name"  # Set a project name

# Define the model
model = ChatOpenAI(
    model="google/gemini-2.5-flash",
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"), 
    base_url=os.getenv("OPENAI_BASE_URL")
)

# Define the node
async def call_model(state: MessagesState):
    messages = state["messages"]
    response = await model.ainvoke(messages)
    return {"messages": [response]}

# Define the graph
workflow = StateGraph(MessagesState)

# Add the node
workflow.add_node("agent", call_model)

# Add edges
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

# Compile
graph = workflow.compile()
