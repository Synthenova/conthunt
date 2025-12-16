from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel

class Chat(BaseModel):
    id: UUID
    user_id: UUID
    thread_id: str
    title: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

class CreateChatRequest(BaseModel):
    title: Optional[str] = None

class SendMessageRequest(BaseModel):
    message: str 

class Message(BaseModel):
    type: str
    content: str
    additional_kwargs: Dict[str, Any] = {}

class ChatHistory(BaseModel):
    messages: List[Message]
