import uuid
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient, models

from app.services.qdrant_service import qdrant_service, QDRANT_COLLECTION_NAME
from app.schemas.chunks import ChunkUpdate
from app.schemas.knowledgebase import EmbeddingModelConfig
from app.db.models.user import User
from app.db.models.knowledgebase import KnowledgeBase
from app.rag.embedding.models import get_embedder as get_rag_embedder

def update_chunk_content(
    db: Session,
    chunk_id: str,
    chunk_in: ChunkUpdate,
    user: User,
) -> models.PointStruct:
    """
    Updates a chunk's content and re-embeds it.
    This is a complex operation as it requires fetching KB context.
    """
    # 1. Retrieve the existing point from Qdrant to get its metadata
    points = qdrant_service.client.retrieve(
        collection_name=QDRANT_COLLECTION_NAME,
        ids=[chunk_id],
        with_payload=True
    )
    if not points:
        raise ValueError("Chunk not found.")
    
    point = points[0]
    payload = point.payload

    # 2. Verify user ownership
    if payload.get("user_id") != str(user.id):
        raise ValueError("User does not have permission to update this chunk.")

    # 3. Fetch the KB to get the embedding configuration
    kb_id = uuid.UUID(payload["kb_id"])
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise ValueError("Associated Knowledge Base not found.")

    # 4. Re-embed the new content using the correct model
    if isinstance(kb.embedding_model, dict):
        embedding_config = EmbeddingModelConfig(**kb.embedding_model)
    else:
        embedding_config = kb.embedding_model
    embedder = get_rag_embedder(config=embedding_config)
    new_embeddings = embedder.embed([chunk_in.content])[0]
    
    # 5. Prepare the updated point for upsert
    payload["chunk_content"] = chunk_in.content
    vector_payload = {k: v for k, v in new_embeddings.items() if v is not None}

    updated_point = models.PointStruct(
        id=chunk_id,
        vector=vector_payload,
        payload=payload
    )

    # 6. Upsert the point (this will overwrite the existing point with the same ID)
    qdrant_service.upsert_single_point(updated_point)
    
    return updated_point