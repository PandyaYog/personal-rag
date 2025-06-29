from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastembed import TextEmbedding, SparseTextEmbedding, LateInteractionTextEmbedding
# from fastembed.late_interaction import LateInteractionTextEmbedding
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from ...schemas.knowledgebase import EmbeddingModelConfig

class ImprovedMultiModelEmbedder:
    """
    Enhanced multi-model embedder with better error handling and model management.
    """
    
    _dense_model_cache: Dict[str, TextEmbedding] = {}
    _sparse_model_cache: Dict[str, SparseTextEmbedding] = {}
    _multi_vector_model_cache: Dict[str, LateInteractionTextEmbedding] = {}
    
    def __init__(self, config: EmbeddingModelConfig):
        """
        Initialize the embedder with proper model configuration.
        
        Args:
            config: EmbeddingModelConfig instance
        """
        self.config = config
        self.dense_model = None
        self.sparse_model = None
        self.multi_vector_model = None
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load all required models with proper error handling."""
        try:
            # Load dense model
            if self.config.dense:
                self.dense_model = self._get_dense_model(self.config.dense)
            
            # Load sparse model
            if self.config.sparse:
                self.sparse_model = self._get_sparse_model(self.config.sparse)
                
            # Load multi-vector model
            if self.config.multi_vector:
                self.multi_vector_model = self._get_multi_vector_model(self.config.multi_vector)
                
        except Exception as e:
            raise
    
    def _get_dense_model(self, model_name: str) -> TextEmbedding:
        """Get or create dense embedding model."""
        if model_name not in self._dense_model_cache:
            try:
                self._dense_model_cache[model_name] = TextEmbedding(
                    model_name=model_name,
                    max_length=512  # Reasonable default
                )
            except Exception as e:
                # Fallback to a reliable model
                fallback_model = "sentence-transformers/all-MiniLM-L6-v2"
                self._dense_model_cache[model_name] = TextEmbedding(model_name=fallback_model)
        
        return self._dense_model_cache[model_name]
    
    def _get_sparse_model(self, model_name: str) -> SparseTextEmbedding:
        """Get or create sparse embedding model."""
        if model_name not in self._sparse_model_cache:
            try:
                self._sparse_model_cache[model_name] = SparseTextEmbedding(
                    model_name=model_name
                )
            except Exception as e:
                # Fallback to a reliable sparse model
                fallback_model = "prithivida/Splade_PP_en_v1"
                self._sparse_model_cache[model_name] = SparseTextEmbedding(model_name=fallback_model)
        
        return self._sparse_model_cache[model_name]
    
    def _get_multi_vector_model(self, model_name: str) -> LateInteractionTextEmbedding:
        """Get or create multi-vector embedding model using FastEmbed's LateInteractionTextEmbedding."""
        if model_name not in self._multi_vector_model_cache:
            try:
                # Use FastEmbed's LateInteractionTextEmbedding for ColBERT-style embeddings
                self._multi_vector_model_cache[model_name] = LateInteractionTextEmbedding(
                    model_name=model_name
                )
            except Exception as e:
                # Fallback to a reliable ColBERT model in FastEmbed
                fallback_model = "colbert-ir/colbertv2.0"
                try:
                    self._multi_vector_model_cache[model_name] = LateInteractionTextEmbedding(
                        model_name=fallback_model
                    )
                except Exception as e2:
                    # If ColBERT fails completely, set to None
                    self._multi_vector_model_cache[model_name] = None
        
        return self._multi_vector_model_cache[model_name]
    
    def embed(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for all configured vector types.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of dictionaries containing embeddings for each text
        """
        if not texts:
            return []
        
        results = []
        
        for i, text in enumerate(texts):
            text_result = {}
            
            # Generate dense embeddings
            if self.dense_model:
                try:
                    dense_embedding = list(self.dense_model.embed([text]))[0]
                    text_result['dense'] = dense_embedding.tolist()
                except Exception as e:
                    text_result['dense'] = None
            
            # Generate sparse embeddings
            if self.sparse_model:
                try:
                    sparse_embedding = list(self.sparse_model.embed([text]))[0]
                    # Convert sparse embedding to proper format
                    if hasattr(sparse_embedding, 'indices') and hasattr(sparse_embedding, 'values'):
                        text_result['sparse'] = {
                            'indices': sparse_embedding.indices.tolist(),
                            'values': sparse_embedding.values.tolist()
                        }
                    else:
                        text_result['sparse'] = sparse_embedding
                except Exception as e:
                    text_result['sparse'] = None
            
            # Generate multi-vector embeddings
            if self.multi_vector_model:
                try:
                    # Use FastEmbed's LateInteractionTextEmbedding for ColBERT-style embeddings
                    multi_vector_embeddings = list(self.multi_vector_model.embed([text]))
                    if multi_vector_embeddings and len(multi_vector_embeddings) > 0:
                        # multi_vector_embeddings[0] should be the ColBERT embedding for the text
                        text_result['multi_vector'] = multi_vector_embeddings[0].tolist()
                    else:
                        text_result['multi_vector'] = None
                except Exception as e:
                    text_result['multi_vector'] = None
            
            results.append(text_result)
        
        return results
    
    def get_dimensions(self) -> Dict[str, int]:
        """Get the dimensions of each embedding type."""
        dims = {}
        
        if self.dense_model:
            # Get dimension from a sample embedding
            sample_embedding = list(self.dense_model.embed(["sample"]))[0]
            dims['dense'] = len(sample_embedding)
        
        if self.multi_vector_model:
            sample_embedding = list(self.multi_vector_model.embed(["sample"]))[0]
            # ColBERT embeddings are typically 3D: [num_tokens, embedding_dim]
            if hasattr(sample_embedding, 'shape'):
                dims['multi_vector'] = sample_embedding.shape[-1]
            else:
                # If it's a list of lists, get the inner dimension
                if isinstance(sample_embedding, list) and len(sample_embedding) > 0:
                    dims['multi_vector'] = len(sample_embedding[0]) if isinstance(sample_embedding[0], list) else len(sample_embedding)
        
        # Sparse dimensions are dynamic, so we don't set a fixed dimension
        dims['sparse'] = None
        
        return dims


def get_embedder(config: EmbeddingModelConfig) -> ImprovedMultiModelEmbedder:
    """
    Factory function to create an embedder instance.
    
    Args:
        config: EmbeddingModelConfig instance
        
    Returns:
        ImprovedMultiModelEmbedder instance
    """
    return ImprovedMultiModelEmbedder(config=config)