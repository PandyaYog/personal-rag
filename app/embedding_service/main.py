from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from fastembed import TextEmbedding, SparseTextEmbedding, LateInteractionTextEmbedding
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Embedding Service")

class EmbeddingModelConfig(BaseModel):
    dense: str = "BAAI/bge-base-en-v1.5"
    sparse: str = "prithivida/Splade_PP_en_v1"
    multi_vector: str = "colbert-ir/colbertv2.0"

class EmbedRequest(BaseModel):
    texts: List[str]
    config: EmbeddingModelConfig

class EmbedResponse(BaseModel):
    embeddings: List[Dict[str, Any]]

_dense_model_cache: Dict[str, TextEmbedding] = {}
_sparse_model_cache: Dict[str, SparseTextEmbedding] = {}
_multi_vector_model_cache: Dict[str, LateInteractionTextEmbedding] = {}

def get_dense_model(model_name: str) -> TextEmbedding:
    if model_name not in _dense_model_cache:
        logger.info(f"Loading dense model: {model_name}")
        _dense_model_cache[model_name] = TextEmbedding(model_name=model_name, max_length=512)
    return _dense_model_cache[model_name]

def get_sparse_model(model_name: str) -> SparseTextEmbedding:
    if model_name not in _sparse_model_cache:
        logger.info(f"Loading sparse model: {model_name}")
        _sparse_model_cache[model_name] = SparseTextEmbedding(model_name=model_name)
    return _sparse_model_cache[model_name]

def get_multi_vector_model(model_name: str) -> LateInteractionTextEmbedding:
    if model_name not in _multi_vector_model_cache:
        logger.info(f"Loading multi-vector model: {model_name}")
        _multi_vector_model_cache[model_name] = LateInteractionTextEmbedding(model_name=model_name)
    return _multi_vector_model_cache[model_name]

@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    results = []
    config = request.config
    logger.info(f"Received embedding request with config: {config}")
    
    dense_model = get_dense_model(config.dense) if config.dense else None
    sparse_model = get_sparse_model(config.sparse) if config.sparse else None
    multi_vector_model = get_multi_vector_model(config.multi_vector) if config.multi_vector else None
    
    for text in request.texts:
        text_result = {}
        
        if dense_model:
            try:
                dense_embedding = list(dense_model.embed([text]))[0]
                text_result['dense'] = dense_embedding.tolist()
            except Exception as e:
                logger.error(f"Dense embedding failed: {e}")
                text_result['dense'] = None
        
        if sparse_model:
            try:
                sparse_embedding = list(sparse_model.embed([text]))[0]
                if hasattr(sparse_embedding, 'indices') and hasattr(sparse_embedding, 'values'):
                    text_result['sparse'] = {
                        'indices': sparse_embedding.indices.tolist(),
                        'values': sparse_embedding.values.tolist()
                    }
                else:
                    text_result['sparse'] = sparse_embedding
            except Exception as e:
                logger.error(f"Sparse embedding failed: {e}")
                text_result['sparse'] = None
                
        if multi_vector_model:
            try:
                mv_embeddings = list(multi_vector_model.embed([text]))
                if mv_embeddings:
                    text_result['multi_vector'] = mv_embeddings[0].tolist()
                else:
                    text_result['multi_vector'] = None
            except Exception as e:
                logger.error(f"Multi-vector embedding failed: {e}")
                text_result['multi_vector'] = None
                
        results.append(text_result)
        
    return EmbedResponse(embeddings=results)

@app.on_event("startup")
async def startup_event():
    logger.info("Pre-loading default models...")
    try:
        get_dense_model("BAAI/bge-base-en-v1.5")
        get_sparse_model("prithivida/Splade_PP_en_v1")
        get_multi_vector_model("colbert-ir/colbertv2.0")
        logger.info("Default models loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load default models: {e}")
