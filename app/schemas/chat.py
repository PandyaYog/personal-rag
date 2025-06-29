import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Message(BaseModel):
    id: uuid.UUID
    role: Literal['user', 'assistant']
    text: str
    is_good: Optional[bool]
    reference_docs: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    name: str = Field("New Chat", min_length=1, max_length=150)

class ChatCreate(BaseModel):
    # Name is optional, will be auto-generated or set to default
    name: Optional[str] = Field(None, min_length=1, max_length=150)

class ChatUpdate(ChatBase):
    pass

class Chat(ChatBase):
    id: uuid.UUID
    assistant_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ChatWithHistory(Chat):
    messages: List[Message]

class UserQuery(BaseModel):
    query: str = Field(..., min_length=1)