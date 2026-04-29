import uuid
import os
from sqlalchemy.orm import Session
from fastapi import UploadFile
from qdrant_client import models
from app.db.models.knowledgebase import Document, KnowledgeBase
from app.db.models.user import User
from app.schemas.document import DocumentUpdate
from app.schemas.chunks import ChunkCreate
from app.schemas.knowledgebase import EmbeddingModelConfig
from app.services.minio_service import minio_client
from app.services.qdrant_service import qdrant_service
from app.rag.embedding.models import get_embedder

def trigger_processing_task(doc_id: str):
    from app.tasks.process_document import process_document_task  
    process_document_task.apply_async(args=[doc_id],
                                task_id=doc_id)
    # process_document_task(doc_id)
    
# --- GET ---
def get_doc_by_id(db: Session, doc_id: uuid.UUID, user_id: uuid.UUID) -> Document | None:
    return db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()

def get_all_docs_in_kb(db: Session, kb_id: uuid.UUID, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(Document)\
        .filter(Document.kb_id == kb_id, Document.user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()

# --- CREATE ---
def upload_document(db: Session, file: UploadFile, kb: KnowledgeBase, user: User):
    """
    Handles uploading a document file to Minio and creating its metadata record in the DB.
    """
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path_in_minio = f"{kb.id}/{unique_filename}"
    
    file_content = file.file.read()
    file_size = len(file_content)
    file.file.seek(0) 

    success = minio_client.upload_file(
        file_path_in_minio=file_path_in_minio,
        file_data=file.file,
        file_size=file_size,
        content_type=file.content_type
    )

    if not success:
        return None

    db_doc = Document(
        name=file.filename,
        kb_id=kb.id,
        user_id=user.id,
        file_path_in_minio=file_path_in_minio,
        file_size=file_size,
        file_extension=file_extension,
        processing_status="PENDING",
    )
    
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    trigger_processing_task(str(db_doc.id))
    print(f"Dispatched processing task for document: {db_doc.id}")
    
    return db_doc

# --- UPDATE ---
def update_document(db: Session, db_doc: Document, doc_in: DocumentUpdate) -> Document:
    update_data = doc_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_doc, field, value)
        
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

# --- DELETE ---
def delete_document(db: Session, db_doc: Document) -> Document:
    """
    Deletes a document and all its associated data:
    - Chunk vectors from the main Qdrant collection
    - Summary vector from the summary Qdrant collection
    - File from Minio object storage
    - Record from PostgreSQL
    """
    doc_id_str = str(db_doc.id)
    
    # Clean up Qdrant chunk vectors
    qdrant_service.delete_points_by_doc_id(doc_id_str)
    
    # Clean up Qdrant summary vector
    try:
        qdrant_service.delete_summary_by_doc_id(doc_id_str)
    except Exception as e:
        # Log but don't block deletion if summary cleanup fails
        print(f"WARNING: Failed to delete summary for doc {doc_id_str}: {e}")
    
    # Clean up Minio file
    minio_client.delete_file(db_doc.file_path_in_minio)
    
    # Remove from database
    db.delete(db_doc)
    db.commit()
    return db_doc

def get_doc_by_id_internal(db: Session, doc_id: uuid.UUID) -> Document | None:
    """Internal getter for Celery worker, does not check user_id."""
    return db.query(Document).filter(Document.id == doc_id).first()

def reprocess_document(db: Session, db_doc: Document):
    """
    Manually triggers reprocessing for an existing document.
    """
    db_doc.processing_status = "PENDING"
    db_doc.num_chunks = 0
    db.commit()

    trigger_processing_task(str(db_doc.id))
    print(f"Dispatched re-processing task for document: {db_doc.id}")
    return db_doc


def add_manual_chunk(db: Session, doc_id: uuid.UUID, chunk_in: ChunkCreate, user: User) -> models.PointStruct:
    """Manually adds a new chunk to a document."""
    doc = get_doc_by_id(db, doc_id=doc_id, user_id=user.id)
    if not doc:
        raise ValueError("Document not found.")

    kb: KnowledgeBase = doc.kb
    if isinstance(kb.embedding_model, dict):
        embedding_config = EmbeddingModelConfig(**kb.embedding_model)
    else:
        embedding_config = kb.embedding_model
    embedder = get_embedder(config=embedding_config)
    embeddings = embedder.embed([chunk_in.content])[0]

    new_point_id = str(uuid.uuid4())
    new_chunk_num = doc.num_chunks + 1
    
    payload = {
        "kb_id": str(kb.id), "doc_id": str(doc.id),
        "doc_name": doc.name, "user_id": str(user.id),
        "chunk_num": new_chunk_num, "chunk_content": chunk_in.content,
    }
    vector_payload = {k: v for k, v in embeddings.items() if v is not None}
    
    new_point = models.PointStruct(id=new_point_id, vector=vector_payload, payload=payload)
    
    qdrant_service.upsert_single_point(new_point)

    doc.num_chunks = new_chunk_num
    db.add(doc)
    db.commit()

    return new_point