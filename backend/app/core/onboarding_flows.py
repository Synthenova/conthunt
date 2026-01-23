"""
Onboarding Flow Definitions

Each flow is a linear tutorial for a specific page.
Flow definitions include step metadata for frontend rendering.
Target selectors are managed in frontend for better separation of concerns.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel


class FlowStep(BaseModel):
    """Single step in a tutorial flow."""
    id: str
    title: str
    content: str
    cta: Optional[dict] = None  # {"label": "Go", "href": "/path"}


class FlowDefinition(BaseModel):
    """Complete definition of a tutorial flow."""
    id: str
    name: str
    page: str
    steps: List[FlowStep]
    
    @property
    def total_steps(self) -> int:
        return len(self.steps)


# Flow definitions - ordered by typical user journey
# NOTE: Target selectors are defined in frontend/src/config/tutorialTargets.ts
ONBOARDING_FLOWS: Dict[str, dict] = {
    "home_tour": {
        "name": "Home Tutorial",
        "page": "/app",
        "steps": [
            {
                "id": "search_input",
                "title": "Type your search",
                "content": "Enter what you're looking for in the search box.",
            },
            {
                "id": "send_button",
                "title": "Hit Enter or Send",
                "content": "Press Enter or click the send button to start your search.",
            },
        ]
    },
    "chat_tour": {
        "name": "Chat Tutorial",
        "page": "/app/chats",
        "steps": [
            {
                "id": "intro",
                "title": "Welcome to Chat",
                "content": "This is where you can explore and analyze your search results."
            },
            {
                "id": "canvas",
                "title": "Your Canvas",
                "content": "The canvas will appear once your search completes with all the results."
            },
            {
                "id": "tabs",
                "title": "Switch Tabs",
                "content": "Click on different tabs to see various views of your results."
            },
            {
                "id": "select_videos",
                "title": "Select Videos",
                "content": "Select multiple videos to perform batch actions."
            },
            {
                "id": "selection_bar",
                "title": "Selection Actions",
                "content": "Use this bar to add selected videos to a board or chat for further analysis."
            },
            {
                "id": "video_click",
                "title": "Click a Video",
                "content": "Click on any video to see its details and preview."
            },
            {
                "id": "analyse",
                "title": "Analyze",
                "content": "Click the analyze button for deep insights on the content."
            },
        ]
    },
    "boards_tour": {
        "name": "Boards Tutorial",
        "page": "/app/boards",
        "steps": [
            {
                "id": "click_board",
                "title": "Open a Board",
                "content": "Click on a board to open it and see its contents."
            },
        ]
    },
    "board_detail_tour": {
        "name": "Board Detail Tutorial",
        "page": "/app/boards/[id]",
        "steps": [
            {
                "id": "videos_tab",
                "title": "Your Saved Videos",
                "content": "All your saved videos appear here."
            },
            {
                "id": "insights_tab",
                "title": "Insights Tab",
                "content": "Click the insights tab to see AI-generated analysis of your board."
            },
            {
                "id": "refresh_insights",
                "title": "Refresh Insights",
                "content": "Click refresh to generate new insights when you add more videos."
            },
        ]
    },
    "profile_tour": {
        "name": "Profile Tutorial",
        "page": "/app/profile",
        "steps": [
            {
                "id": "streak",
                "title": "Maintain Your Streak",
                "content": "Open the app daily to build your streak and earn rewards!"
            },
        ]
    },
}


def get_flow(flow_id: str) -> Optional[FlowDefinition]:
    """Get a flow definition by ID."""
    if flow_id not in ONBOARDING_FLOWS:
        return None
    
    flow_data = ONBOARDING_FLOWS[flow_id]
    return FlowDefinition(
        id=flow_id,
        name=flow_data["name"],
        page=flow_data["page"],
        steps=[FlowStep(**step) for step in flow_data["steps"]]
    )


def get_all_flows() -> List[FlowDefinition]:
    """Get all flow definitions."""
    return [get_flow(flow_id) for flow_id in ONBOARDING_FLOWS]
