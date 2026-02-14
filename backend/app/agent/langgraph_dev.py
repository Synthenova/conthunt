"""LangGraph dev entrypoints for local testing."""
from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_graph
from app.agent.deep_agent import build_deep_agent

_memory_saver = MemorySaver()

# Deep agent graph (Deep Research mode)
deep_agent_graph = build_deep_agent()
