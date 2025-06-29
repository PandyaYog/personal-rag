import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from .knowledgebase import EmbeddingModelConfig

class LinkedKnowledgeBase(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True

SEARCH_METHODS = Literal[
    "dense", "sparse", "multi_vector", "hybrid_dense_sparse", "dense_rerank_multi",
    "sparse_rerank_multi", "rrf", "full_rrf"
]
class LLMConfig(BaseModel):
    provider: str = Field("groq", example="groq")
    model: str = Field("llama3-8b-8192", example="llama3-8b-8192")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    system_prompt: str = Field(
        "You are a helpful assistant. Use the provided context to answer the user's query accurately. "
        "If the context does not contain the answer, state that you don't have enough information.",
        example="You are a helpful assistant..."
    )
    search_type: SEARCH_METHODS = Field("full_rrf", description="The search strategy to use for retrieval.")

class AssistantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Project Q&A Bot")

class AssistantCreate(AssistantBase):
    knowledge_base_ids: List[uuid.UUID] = Field(..., description="List of KB IDs to connect to this assistant.")
    llm_config: Optional[LLMConfig] = None # Optional on create, will use defaults
    embedding_config: Optional[EmbeddingModelConfig] = None

class AssistantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    knowledge_base_ids: Optional[List[uuid.UUID]] = None
    llm_config: Optional[LLMConfig] = None
    embedding_config: Optional[EmbeddingModelConfig] = None

class Assistant(AssistantBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]
    num_chats: int = Field(0, description="Total number of chats for this assistant.")
    knowledge_bases: List[LinkedKnowledgeBase] = Field([], description="List of connected knowledge bases.")
    llm_config: LLMConfig
    embedding_config: EmbeddingModelConfig
    class Config:
        from_attributes = True  