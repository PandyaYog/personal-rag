from typing import List, Dict, Any, Optional
from ...schemas.knowledgebase import EmbeddingModelConfig
from .client import RemoteEmbedder

def get_embedder(config: EmbeddingModelConfig):
    """
    Factory function to create an embedder instance.
    Returns a RemoteEmbedder that communicates with the dedicated embedding service.
    """
    return RemoteEmbedder(config=config)