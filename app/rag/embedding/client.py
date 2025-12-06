import httpx
from typing import List, Dict, Any
from app.schemas.knowledgebase import EmbeddingModelConfig
from app.core.config import settings

class RemoteEmbedder:
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self.service_url = settings.EMBEDDING_SERVICE_URL

    def embed(self, texts: List[str]) -> List[Dict[str, Any]]:
        if not texts:
            return []
            
        payload = {
            "texts": texts,
            "config": self.config.model_dump()
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(f"{self.service_url}/embed", json=payload, timeout=60.0)
                response.raise_for_status()
                return response.json()['embeddings']
        except Exception as e:
            logger.error(f"Error calling embedding service: {e}")
            raise
