import uuid
from datetime import datetime
from pydantic import BaseModel, Field, conint
from typing import Literal, Dict, Any

class HybridChunkingConfig(BaseModel):
    strategy: Literal["hybrid"] = "hybrid"
    semantic_model: str = Field("all-MiniLM-L6-v2", description="Model for semantic splitting.")
    token_size: conint(gt=0) = Field(500, description="Target token size for chunks.")

ChunkingConfig = HybridChunkingConfig 

class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="My First KB")
    description: str | None = Field(None, max_length=500, example="A knowledge base about my projects.")

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(KnowledgeBaseBase):
    pass

class KnowledgeBaseConfigUpdate(BaseModel):
    embedding_model: str | None = Field(None, example="all-MiniLM-L6-v2")
    chunking_strategy: ChunkingConfig | None = None
    
class KnowledgeBase(KnowledgeBaseBase):
    id: uuid.UUID
    avatar: str | None
    created_at: datetime
    updated_at: datetime | None
    num_documents: int = Field(0, description="Total number of documents in the KB.")
    num_processed_documents: int = Field(0, description="Number of successfully processed documents.")

    class Config:
        from_attributes = True

class KnowledgeBaseWithConfig(KnowledgeBase):
    embedding_model: str
    chunking_strategy: Dict[str, Any]