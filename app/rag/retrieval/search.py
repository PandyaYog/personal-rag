from qdrant_client import models
from app.services.qdrant_service import qdrant_service, QDRANT_COLLECTION_NAME
from app.rag.embedding.models import get_embedder as get_rag_embedder
from typing import List, Dict, Any

class AdvancedRetriever:
    def __init__(self, embedding_config: Dict[str, str]):
        self.embedder = get_rag_embedder(config=embedding_config)
        self.client = qdrant_service.client

    def search(self, query: str, filters: models.Filter, search_type: str, top_k: int = 10) -> List[models.ScoredPoint]:
        """Main search dispatcher that routes to the correct search method."""
        query_embeddings = self.embedder.embed([query])[0]
        
        dispatch_table = {
            "dense": self._dense_search,
            "sparse": self._sparse_search,
            "multi_vector": self._multi_vector_search,
            "hybrid_dense_sparse": self._hybrid_dense_sparse_search,
            "dense_rerank_multi": self._rerank_search,
            "sparse_rerank_multi": lambda qe, f, k: self._rerank_search(qe, f, k, prefetch_vectors=["sparse"]),
            "rrf": lambda qe, f, k: self._rrf_search(qe, f, k, vectors=["dense", "sparse"]),
            "full_rrf": lambda qe, f, k: self._rrf_search(qe, f, k, vectors=["dense", "sparse", "multi_vector"]),
        }
        
        search_method = dispatch_table.get(search_type)
        if not search_method:
            raise NotImplementedError(f"Search type '{search_type}' is not implemented.")
            
        return search_method(query_embeddings, filters, top_k)

    # --- Basic Search Methods ---
    def _dense_search(self, qe, f, k):
        result = self.client.query_points(collection_name=QDRANT_COLLECTION_NAME, query=qe['dense'], using="dense", query_filter=f, limit=k, with_payload=True)
        return result.points

    def _sparse_search(self, qe, f, k):
        sparse_vector = qe['sparse']
        if isinstance(sparse_vector, dict):
            sparse_vector = models.SparseVector(indices=sparse_vector['indices'], values=sparse_vector['values'])
        result = self.client.query_points(collection_name=QDRANT_COLLECTION_NAME, query=sparse_vector, using="sparse", query_filter=f, limit=k, with_payload=True)
        return result.points

    def _multi_vector_search(self, qe, f, k):
        multi_vector = qe['multi_vector']
        if isinstance(multi_vector, list) and len(multi_vector) > 0 and isinstance(multi_vector[0], list):
            if len(multi_vector) == 1:
                multi_vector = multi_vector[0]
            else:
                import numpy as np
                multi_vector = np.mean(multi_vector, axis=0).tolist()
        elif isinstance(multi_vector, list) and len(multi_vector) == 896:
            multi_vector = multi_vector[:128]
        
        result = self.client.query_points(collection_name=QDRANT_COLLECTION_NAME, query=multi_vector, using="multi_vector", query_filter=f, limit=k, with_payload=True)
        return result.points
    # --- Advanced Search Methods ---
    def _hybrid_dense_sparse_search(self, qe, f, k):
        """Performs two separate searches and combines the results (simple approach)."""
        dense_hits = self._dense_search(qe, f, k)
        sparse_hits = self._sparse_search(qe, f, k)
        
        all_hits = {hit.id: hit for hit in dense_hits}
        all_hits.update({hit.id: hit for hit in sparse_hits})
        
        return sorted(all_hits.values(), key=lambda x: x.score, reverse=True)[:k]

    def _rerank_search(self, qe, f, k, prefetch_vectors: List[str] = ["dense", "sparse"]):
        """
        General reranking implementation. Prefetches with a list of vectors, reranks with another.
        Your 'dense + sparse to prefetch and multi vector for selection' is a specific case of this.
        """
        prefetch = []
        for vec_name in prefetch_vectors:
            if vec_name == "sparse":
                sparse_vector = qe[vec_name]
                if isinstance(sparse_vector, dict):
                    sparse_vector = models.SparseVector(indices=sparse_vector['indices'], values=sparse_vector['values'])
                prefetch.append(models.Prefetch(query=sparse_vector, using=vec_name, limit=30, filter=f))
            else:
                prefetch.append(models.Prefetch(query=qe[vec_name], using=vec_name, limit=30, filter=f))
            
        result = self.client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            prefetch=prefetch,
            query=qe['multi_vector'],
            using="multi_vector",
            query_filter=f, with_payload=True, limit=k
        )
        return result.points

    def _rrf_search(self, qe, f, k, vectors: List[str] = ["dense", "sparse", "multi_vector"]):
        """
        General Reciprocal Rank Fusion implementation.
        Handles both 'rrf' and 'full_rrf'.
        """
        prefetch = []
        for vec_name in vectors:
            if vec_name == "sparse":
                sparse_vector = qe[vec_name]
                if isinstance(sparse_vector, dict):
                    sparse_vector = models.SparseVector(indices=sparse_vector['indices'], values=sparse_vector['values'])
                prefetch.append(models.Prefetch(query=sparse_vector, using=vec_name, limit=50, filter=f))
            else:
                prefetch.append(models.Prefetch(query=qe[vec_name], using=vec_name, limit=50, filter=f))
            
        result = self.client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=f, with_payload=True, limit=k
        )
        return result.points

def get_retriever(embedding_config: Dict[str, str]) -> AdvancedRetriever:
    return AdvancedRetriever(embedding_config)