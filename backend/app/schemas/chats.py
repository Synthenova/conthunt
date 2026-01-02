from datetime import datetime
from uuid import UUID
from typing import Union, List, Dict, Any, Optional, Literal
from pydantic import BaseModel
from langchain_core.messages import (
    BaseMessage, 
    AnyMessage,
)

# Define ContentBlock type broadly since it's often a complex Union or specific to implementation.
# But user requested ContentBlock import. Let's trust the import works as verified.
# However, Pydantic needs actual types.
# If ContentBlock is a TypeAlias, we can use it.
from langchain_core.messages import ContentBlock

# Precise content type matching LangChain
ContentType = Union[
    str,                                    # Simple text
    List[ContentBlock],                     # Multimodal content blocks
    Dict[str, Any],                         # Fallback for structured dicts
]

class Chat(BaseModel):
    id: UUID
    user_id: UUID
    thread_id: str
    title: Optional[str] = None
    context_type: Optional[Literal["board", "search"]] = None
    context_id: Optional[UUID] = None
    status: str
    created_at: datetime
    updated_at: datetime

class CreateChatRequest(BaseModel):
    title: Optional[str] = None
    context_type: Optional[Literal["board", "search"]] = None
    context_id: Optional[UUID] = None

class SendMessageRequest(BaseModel):
    message: str
    client_id: Optional[str] = None

class Message(BaseModel):
    id: Optional[str] = None
    type: str
    content: ContentType
    additional_kwargs: Dict[str, Any] = {}

class ChatHistory(BaseModel):
    messages: List[Message]
