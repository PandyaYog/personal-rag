from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from app.core.config import settings
from typing import List, Optional

DENSE_DIM = 768
MULTI_VECTOR_DIM = 128
QDRANT_COLLECTION_NAME = "rag_from_scratch_collection"
SUMMARY_COLLECTION_NAME = "document_summaries"


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=180.0
        )
        self._ensure_collection_exists()
        self._ensure_summary_collection_exists()
        self._ensure_payload_indexes()

    # ─── Collection Initialization ────────────────────────────────────────────

    def _ensure_collection_exists(self):
        """
        Creates the main chunk collection in Qdrant if it doesn't exist,
        configured for dense, sparse, and multi-vector storage.
        """
        try:
            self.client.get_collection(collection_name=QDRANT_COLLECTION_NAME)
            print(f"Collection '{QDRANT_COLLECTION_NAME}' already exists.")
            return
        except UnexpectedResponse as e:
            if e.status_code != 404:
                raise
            print(f"Collection '{QDRANT_COLLECTION_NAME}' not found. Creating...")
        except Exception:
            print(f"Collection '{QDRANT_COLLECTION_NAME}' not found. Creating...")

        try:
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
        except UnexpectedResponse as e:
            if e.status_code == 409:
                print(f"Collection '{QDRANT_COLLECTION_NAME}' was created by another worker. Skipping.")
            else:
                raise

    def _ensure_payload_indexes(self):
        """
        Creates payload indexes required by Qdrant Cloud for filtered queries.
        """
        chunk_index_fields = {
            "doc_id": models.PayloadSchemaType.KEYWORD,
            "kb_id": models.PayloadSchemaType.KEYWORD,
            "user_id": models.PayloadSchemaType.KEYWORD,
        }
        for field_name, field_type in chunk_index_fields.items():
            try:
                self.client.create_payload_index(
                    collection_name=QDRANT_COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except UnexpectedResponse as e:
                if e.status_code != 409:
                    print(f"WARNING: Failed to create index '{field_name}': {e}")
            except Exception as e:
                print(f"WARNING: Failed to create index '{field_name}': {e}")

        summary_index_fields = {
            "doc_id": models.PayloadSchemaType.KEYWORD,
            "kb_id": models.PayloadSchemaType.KEYWORD,
            "user_id": models.PayloadSchemaType.KEYWORD,
        }
        for field_name, field_type in summary_index_fields.items():
            try:
                self.client.create_payload_index(
                    collection_name=SUMMARY_COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except UnexpectedResponse as e:
                if e.status_code != 409:
                    print(f"WARNING: Failed to create index '{field_name}': {e}")
            except Exception as e:
                print(f"WARNING: Failed to create index '{field_name}': {e}")

    def _ensure_summary_collection_exists(self):
        """
        Creates a dedicated collection for document summaries if it doesn't exist.
        Uses dense vectors only — summaries are retrieved by metadata filters (doc_id),
        not by semantic similarity search, so sparse/multi-vector are unnecessary.
        """
        try:
            self.client.get_collection(collection_name=SUMMARY_COLLECTION_NAME)
            print(f"Summary collection '{SUMMARY_COLLECTION_NAME}' already exists.")
            return
        except UnexpectedResponse as e:
            if e.status_code != 404:
                raise
            print(f"Summary collection '{SUMMARY_COLLECTION_NAME}' not found. Creating...")
        except Exception:
            print(f"Summary collection '{SUMMARY_COLLECTION_NAME}' not found. Creating...")

        try:
            self.client.create_collection(
                    collection_name=SUMMARY_COLLECTION_NAME,
                    vectors_config={
                        "dense": models.VectorParams(
                            size=DENSE_DIM,
                            distance=models.Distance.COSINE
                        ),
                    },
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                ),
            )
            print(f"Summary collection '{SUMMARY_COLLECTION_NAME}' created successfully.")
        except UnexpectedResponse as e:
            if e.status_code == 409:
                print(f"Summary collection '{SUMMARY_COLLECTION_NAME}' was created by another worker. Skipping.")
            else:
                print(f"ERROR: Failed to create summary collection: {e}")
                raise
        except Exception as e:
            print(f"ERROR: Failed to create summary collection: {e}")
            raise

    # ─── Chunk Collection Operations ──────────────────────────────────────────

    def upsert_points(self, points):
        """Upserts points into the main chunk collection."""
        self.client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points,
            wait=True
        )

    def get_chunks_for_document(self, doc_id: str) -> List[models.ScoredPoint]:
        """
        Retrieves all chunk points for a specific document ID using scrolling.
        """
        points, _ = self.client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False 
        )
        return points
    
    def delete_points_by_doc_id(self, doc_id: str):
        """Deletes all chunk points associated with a specific document ID."""
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
        print(f"Deleted all chunk points for doc_id: {doc_id} from Qdrant.")

    def upsert_single_point(self, point: models.PointStruct):
        """Upserts a single point, useful for updating or adding a chunk."""
        self.client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[point],
            wait=True
        )

    # ─── Summary Collection Operations ────────────────────────────────────────

    def upsert_summary_point(self, point: models.PointStruct) -> None:
        """
        Upserts a single summary point into the dedicated summary collection.
        
        Args:
            point: A PointStruct containing the dense vector and payload with
                   keys: kb_id, doc_id, doc_name, user_id, summary_text, 
                   summary_method, chunk_count.
        """
        try:
            self.client.upsert(
                collection_name=SUMMARY_COLLECTION_NAME,
                points=[point],
                wait=True
            )
            print(f"Upserted summary for doc_id: {point.payload.get('doc_id', 'unknown')}")
        except Exception as e:
            print(f"ERROR: Failed to upsert summary point: {e}")
            raise

    def get_summary_by_doc_id(self, doc_id: str) -> Optional[models.Record]:
        """
        Retrieves the summary point for a specific document from the summary collection.
        
        Args:
            doc_id: The UUID string of the document.
            
        Returns:
            The summary Record if found, otherwise None.
        """
        try:
            points, _ = self.client.scroll(
                collection_name=SUMMARY_COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="doc_id",
                            match=models.MatchValue(value=doc_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            return points[0] if points else None
        except Exception as e:
            print(f"ERROR: Failed to retrieve summary for doc_id {doc_id}: {e}")
            return None

    def delete_summary_by_doc_id(self, doc_id: str) -> None:
        """
        Deletes the summary point associated with a specific document ID 
        from the summary collection. Called during document deletion or reprocessing.
        
        Args:
            doc_id: The UUID string of the document whose summary should be removed.
        """
        try:
            self.client.delete(
                collection_name=SUMMARY_COLLECTION_NAME,
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
            print(f"Deleted summary for doc_id: {doc_id} from summary collection.")
        except Exception as e:
            print(f"ERROR: Failed to delete summary for doc_id {doc_id}: {e}")
            raise


qdrant_service = QdrantService()