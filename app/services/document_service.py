import uuid
import os
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.db.models.knowledgebase import Document, KnowledgeBase
from app.db.models.user import User
from app.schemas.document import DocumentUpdate
from app.services.minio_service import minio_client

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
    minio_client.delete_file(db_doc.file_path_in_minio)
    db.delete(db_doc)
    db.commit()
    return db_doc