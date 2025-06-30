import uuid
from datetime import datetime
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Literal, Dict, Any

class Message(BaseModel):
    id: uuid.UUID
    role: Literal['user', 'assistant']
    content: Dict[str, Any]
    is_good: Optional[bool]
    created_at: datetime

    @computed_field
    @property
    def text(self) -> str:
        """Returns the text of the latest version. This now works for all roles."""
        return self.content["versions"][-1]["text"]

    @computed_field
    @property
    def reference_docs(self) -> Optional[List[str]]:
        return self.content["versions"][-1].get("reference_docs")
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

class Feedback(BaseModel):
    is_good: bool