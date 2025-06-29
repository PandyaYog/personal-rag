from qdrant_client import QdrantClient, models
from app.core.config import settings
import httpx
# from app.rag.embedding.models import DENSE_DIM, MULTI_VECTOR_DIM

DENSE_DIM = 384
MULTI_VECTOR_DIM = 128
QDRANT_COLLECTION_NAME = "rag_from_scratch_collection"

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=180.0)
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """
        Creates the main collection in Qdrant if it doesn't exist,
        configured for dense, sparse, and multi-vector storage.
        """
        try:
            self.client.get_collection(collection_name=QDRANT_COLLECTION_NAME)
            print(f"Collection '{QDRANT_COLLECTION_NAME}' already exists.")
        except Exception:
            print(f"Collection '{QDRANT_COLLECTION_NAME}' not found. Creating...")
            self.client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config={
                    "dense": models.VectorParams(
                        size=DENSE_DIM, 
                        distance=models.Distance.COSINE
                    ),
                    "multi_vector": models.VectorParams(
                        size = MULTI_VECTOR_DIM,
                        distance = models.Distance.DOT,
                        multivector_config=models.MultiVectorConfig(
                            comparator = models.MultiVectorComparator.MAX_SIM
                        ),
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False, 
                        )
                    )
                },
                hnsw_config=models.HnswConfigDiff(
                    m=16, 
                    ef_construct=100, 
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    ),
                ),
            )
            
            print("Collection created successfully with dense, sparse, and multi-vector configs.")

    def upsert_points(self, points):
        """Upserts points into the collection."""
        self.client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points,
            wait=True
        )

    def delete_points_by_doc_id(self, doc_id: str):
        """Deletes all points associated with a specific document ID."""
        self.client.delete(
            collection_name=QDRANT_COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="doc_id",
                            match=models.MatchValue(value=doc_id),
                        ),
                    ]
                )
            ),
        )
        print(f"Deleted all points for doc_id: {doc_id} from Qdrant.")

qdrant_service = QdrantService()