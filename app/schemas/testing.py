import uuid
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from app.schemas.knowledgebase import EmbeddingModelConfig, FixedSizeChunkerParams, SentenceBasedChunkerParams, SemanticChunkerParams, SlidingWindowChunkerParams, TokenBasedChunkerParams, HybridChunkerParams, RecursiveChunkerParams
from app.schemas.assistant import SEARCH_METHODS

CHUNK_PARAMS_MAP = {
    "fixed_size": FixedSizeChunkerParams,
    "sentence_based": SentenceBasedChunkerParams,
    "semantic_based": SemanticChunkerParams,
    "sliding_window": SlidingWindowChunkerParams,
    "token_based": TokenBasedChunkerParams,
    "hybrid": HybridChunkerParams,
    "recursive": RecursiveChunkerParams
}

# --- Schemas for the Chunking Tester Endpoint ---
class ChunkingTestRequest(BaseModel):
    text_content: str = Field(..., min_length=1, description="The raw text content to be chunked.")
    strategy: Literal[
        "fixed_size", "sentence_based", "semantic_based", 
        "sliding_window", "token_based", "hybrid", "recursive"
    ] = Field(..., description="The name of the chunking strategy to use.")
    parameters: Dict[str, Any] = Field({}, description="A dictionary of parameters for the chosen strategy.")

class ChunkingTestResponse(BaseModel):
    total_chunks: int = Field(..., description="The total number of chunks created.")
    avg_chunk_length_chars: float = Field(..., description="The average character length of the chunks.")
    avg_chunk_length_tokens: float = Field(..., description="The average token length of the chunks (using cl100k_base).")
    chunks: List[str] = Field(..., description="The list of generated text chunks.")


# --- Schemas for the Retrieval Tester Endpoint ---
class RetrievalTestRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user query to test retrieval against.")
    search_type: SEARCH_METHODS = Field(..., description="The search strategy to use.")
    knowledge_base_ids: List[uuid.UUID] = Field(..., description="A list of Knowledge Base IDs to search within.")
    embedding_config: Optional[EmbeddingModelConfig] = Field(
        None, 
        description="Optional. The embedding configuration for the query. If null, assistant's default is used (though not applicable in this stateless tester)."
    )

class RetrievedChunk(BaseModel):
    chunk_id: str = Field(..., description="The unique ID of the chunk in the vector database.")
    content: str = Field(..., description="The text content of the retrieved chunk.")
    source_document_name: str = Field(..., description="The name of the document this chunk belongs to.")
    retrieval_score: float = Field(..., description="The relevance score assigned by the retrieval system.")

class RetrievalTestResponse(BaseModel):
    retrieved_chunks: List[RetrievedChunk]