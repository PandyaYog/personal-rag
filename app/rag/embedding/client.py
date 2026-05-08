import httpx
from typing import List, Dict, Any
import logging
from app.schemas.knowledgebase import EmbeddingModelConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        
        headers = {
            "X-API-Key": settings.EMBEDDING_SERVICE_API_KEY,
            "Authorization": f"Bearer {settings.EMBEDDING_SERVICE_API_KEY}"
        }
        
        import time
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                with httpx.Client() as client:
                    response = client.post(f"{self.service_url}/embed", json=payload, headers=headers, timeout=180.0)
                    
                    if response.status_code == 429:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limited (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                        
                    response.raise_for_status()
                    return response.json()['embeddings']
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    continue
                logger.error(f"Error calling embedding service: {e}")
                raise
            except Exception as e:
                logger.error(f"Error calling embedding service: {e}")
                raise
        
        raise Exception("Failed to get embeddings after multiple retries due to rate limiting.")
