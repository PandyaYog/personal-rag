import tiktoken
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from qdrant_client import models

from fastembed import TextEmbedding
from app.schemas.testing import ChunkingTestRequest, RetrievalTestRequest, CHUNK_PARAMS_MAP, EmbeddingRelevanceTestRequest, EmbeddingRelevanceResult
from app.db.models.user import User
from app.rag.chunking.methods import get_chunker
from app.rag.retrieval.search import get_retriever
from app.schemas.knowledgebase import EmbeddingModelConfig

default_tokenizer = tiktoken.get_encoding("cl100k_base")

def test_chunking_strategy(request: ChunkingTestRequest) -> Dict[str, Any]:
    """
    Applies a given chunking strategy to text and returns the chunks and statistics.
    This is a stateless function.
    """
    # 1. Validate and merge parameters with defaults
    params_model = CHUNK_PARAMS_MAP.get(request.strategy)
    if not params_model:
        raise ValueError(f"Invalid chunking strategy '{request.strategy}' provided.")
    
    default_params = params_model()
    merged_params = default_params.model_dump()
    merged_params.update(request.parameters)

    # 2. Build the full strategy configuration for the factory function
    strategy_config = {
        "strategy": request.strategy,
        **merged_params
    }
    
    # 3. Instantiate the chunker and generate chunks
    chunker = get_chunker(strategy_config)
    chunks = chunker.chunk(request.text_content)
    
    # 4. Calculate statistics
    if not chunks:
        return {
            "total_chunks": 0,
            "avg_chunk_length_chars": 0.0,
            "avg_chunk_length_tokens": 0.0,
            "chunks": []
        }
        
    char_lengths = [len(c) for c in chunks]
    token_lengths = [len(default_tokenizer.encode(c)) for c in chunks]
    
    response = {
        "total_chunks": len(chunks),
        "avg_chunk_length_chars": np.mean(char_lengths),
        "avg_chunk_length_tokens": np.mean(token_lengths),
        "chunks": chunks
    }
    
    return response

def test_retrieval_strategy(
    db: Session, 
    request: RetrievalTestRequest, 
    user: User
) -> List[Dict[str, Any]]:
    """
    Tests a retrieval strategy against specified knowledge bases for a user.
    """
    # 1. Determine the embedding configuration to use
    try:
        embedding_config_data = (
            request.embedding_config.model_dump() if request.embedding_config else EmbeddingModelConfig().model_dump()
        )
        embedding_config_model = EmbeddingModelConfig(**embedding_config_data)
    except Exception as e:
        raise ValueError(f"Invalid embedding configuration for testing: {e}")

    # 2. Instantiate the retriever with the specified config
    retriever = get_retriever(embedding_config=embedding_config_model)

    # 3. Build the search filter based on user and KB IDs
    kb_ids_as_str = [str(kb_id) for kb_id in request.knowledge_base_ids]
    search_filter = models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user.id))),
            models.FieldCondition(key="kb_id", match=models.MatchAny(any=kb_ids_as_str))
        ]
    )

    # 4. Perform the search using the specified strategy
    search_results = retriever.search(
        query=request.query,
        filters=search_filter,
        search_type=request.search_type
    )

    # 5. Format the results for the response schema
    formatted_chunks = []
    for hit in search_results:
        payload = hit.payload
        formatted_chunks.append({
            "chunk_id": hit.id,
            "content": payload.get("chunk_content", ""),
            "source_document_name": payload.get("doc_name", "Unknown"),
            "retrieval_score": hit.score
        })
        
    return formatted_chunks

# --- Embedding Relevance Test Logic ---

_model_cache: Dict[str, TextEmbedding] = {}

def _get_cached_model(model_name: str) -> TextEmbedding:
    """
    Get or create a cached TextEmbedding model.
    """
    if model_name not in _model_cache:
        # We use a default max_length or let it be default
        _model_cache[model_name] = TextEmbedding(model_name=model_name)
    return _model_cache[model_name]

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

def test_embedding_relevance(request: EmbeddingRelevanceTestRequest) -> List[EmbeddingRelevanceResult]:
    """
    Tests multiple embedding models on their ability to differentiate 
    between a positive and negative passage for a given query.
    """
    results = []
    
    # Texts to embed: query, positive, negative
    texts = [request.query, request.positive_passage, request.negative_passage]
    
    for model_name in request.models_to_test:
        try:
            model = _get_cached_model(model_name)
            
            # Embed all 3 texts in one batch
            # fastembed returns a generator, convert to list
            embeddings = list(model.embed(texts))
            
            if len(embeddings) != 3:
                # Should not happen if successful
                continue
                
            query_vec = embeddings[0]
            pos_vec = embeddings[1]
            neg_vec = embeddings[2]
            
            pos_score = cosine_similarity(query_vec, pos_vec)
            neg_score = cosine_similarity(query_vec, neg_vec)
            diff_score = pos_score - neg_score
            
            results.append(EmbeddingRelevanceResult(
                model_name=model_name,
                positive_score=pos_score,
                negative_score=neg_score,
                differentiation_score=diff_score
            ))
            
        except Exception as e:
            # If a model fails to load or embed, we can skip it or report error.
            # For now, we'll skip or could return a result with 0 scores and error note if schema supported it.
            # We'll just print/log and continue to next model.
            print(f"Error testing model {model_name}: {e}")
            continue
            
    return results