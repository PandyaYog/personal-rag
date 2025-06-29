import uuid
from datetime import datetime
from pydantic import BaseModel, Field, conint
from typing import Literal, Dict, Any, Union, List, Optional

class FixedSizeChunkerParams(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 100

class SentenceBasedChunkerParams(BaseModel):
    max_chunk_size: int | None = 1024

class SemanticChunkerParams(BaseModel):
    embedding_model: str = 'all-MiniLM-L6-v2'
    backend: str = 'sentence_transformers'
    breakpoint_percentile: int = 90
    buffer_size: int = 1

class SlidingWindowChunkerParams(BaseModel):
    window_size: int = 1000
    step_size: int = 500
    unit: Literal['char', 'word', 'sentence'] = 'char'

class TokenBasedChunkerParams(BaseModel):
    token_size: int = 500
    token_overlap: int = 50
    model_name: str = "cl100k_base"
    tokenizer_backend: str = "tiktoken"

class RecursiveChunkerParams(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 100
    separators: List[str] = ["\n\n", "\n", ". ", " ", ""]

class HybridChunkerParams(BaseModel):
    embedding_model: str = 'all-MiniLM-L6-v2'
    backend: str = 'sentence_transformers'
    breakpoint_percentile: int = 90
    buffer_size: int = 1
    token_size: int = 512
    token_overlap: int = 50 
    model_name: str = "cl100k_base"
    tokenizer_backend: str = "tiktoken"

# --- Main Chunking Strategy Schema using a Union of all parameter types ---
AnyChunkerParams = Union[
    FixedSizeChunkerParams, SentenceBasedChunkerParams, SemanticChunkerParams, 
    SlidingWindowChunkerParams, TokenBasedChunkerParams, HybridChunkerParams, 
    RecursiveChunkerParams
]

class ChunkingStrategy(BaseModel):
    strategy: Literal[
        "fixed_size", "sentence_based", "semantic_based", 
        "sliding_window", "token_based", "hybrid", "recursive"
    ]
    parameters: Dict[str, Any]

class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="My First KB")
    description: str | None = Field(None, max_length=500, example="A knowledge base about my projects.")

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(KnowledgeBaseBase):
    pass

class EmbeddingModelConfig(BaseModel):
    dense: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", 
        description="Model for dense vector embeddings. FastEmbed compatible."
    )
    sparse: str = Field(
        "prithivida/Splade_PP_en_v1", 
        description="Model for sparse vector embeddings (SPLADE). FastEmbed compatible."
    )
    multi_vector: str = Field(
        "colbert-ir/colbertv2.0", 
        description="Model for multi-vector embeddings (FastEmbed ColBERT)"
    )

    dense_dim: Optional[int] = Field(None, description="Dense embedding dimension")
    sparse_dim: Optional[int] = Field(None, description="Sparse embedding dimension") 
    multi_vector_dim: Optional[int] = Field(None, description="Multi-vector embedding dimension")

class KnowledgeBaseConfigUpdate(BaseModel):
    embedding_model: EmbeddingModelConfig | None = None
    chunking_strategy: ChunkingStrategy | None = None

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
    embedding_model: EmbeddingModelConfig
    chunking_strategy: ChunkingStrategy