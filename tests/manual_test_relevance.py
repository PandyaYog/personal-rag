import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock dependencies that require DB connection
sys.modules["app.services.qdrant_service"] = MagicMock()
sys.modules["app.rag.retrieval.search"] = MagicMock()

from app.schemas.testing import EmbeddingRelevanceTestRequest
from app.services.testing_service import test_embedding_relevance

def run_test():
    print("Starting manual embedding relevance test...")
    
    # Define test data
    request = EmbeddingRelevanceTestRequest(
        models_to_test=["BAAI/bge-small-en-v1.5"], # Small model for quick test
        query="What is the capital of France?",
        positive_passage="Paris is the capital and most populous city of France.",
        negative_passage="The quick brown fox jumps over the lazy dog."
    )
    
    try:
        results = test_embedding_relevance(request)
        
        print(f"\nTest completed. Received {len(results)} results.")
        for res in results:
            print(f"\nModel: {res.model_name}")
            print(f"Positive Score: {res.positive_score:.4f}")
            print(f"Negative Score: {res.negative_score:.4f}")
            print(f"Differentiation: {res.differentiation_score:.4f}")
            
            if res.differentiation_score > 0.3:
                print("SUCCESS: Good differentiation observed.")
            else:
                print("WARNING: Low differentiation.")
                
    except Exception as e:
        print(f"Test FAILED with error: {e}")

if __name__ == "__main__":
    run_test()
