from abc import ABC, abstractmethod
from typing import List, Any

class BaseEmbedder(ABC):
    """Abstract base class for all embedding models."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a list of texts."""
        pass
    