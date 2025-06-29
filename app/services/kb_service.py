import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import json
from app.db.models.knowledgebase import KnowledgeBase, Document
from app.db.models.user import User
from app.schemas.knowledgebase import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseConfigUpdate, HybridChunkerParams, EmbeddingModelConfig
from app.services.minio_service import minio_client

# --- GET ---
def get_kb_by_id(db: Session, kb_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeBase | None:
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == user_id).first()

def get_all_kbs_for_user(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(
        KnowledgeBase,
        func.count(Document.id).label("num_documents"),
        func.sum(case((Document.processing_status == 'COMPLETED', 1), else_=0)).label("num_processed_documents")
    ).outerjoin(Document, KnowledgeBase.id == Document.kb_id)\
     .filter(KnowledgeBase.user_id == user_id)\
     .group_by(KnowledgeBase.id)\
     .offset(skip)\
     .limit(limit)\
     .all()

# --- CREATE ---
def create_kb(db: Session, kb_in: KnowledgeBaseCreate, user: User) -> KnowledgeBase:
    default_hybrid_params = HybridChunkerParams().model_dump()
    default_chunking = {
        "strategy": "hybrid",
        "parameters": default_hybrid_params
    }
    default_embedding_config = EmbeddingModelConfig().model_dump()

    db_kb = KnowledgeBase(
        **kb_in.model_dump(),
        user_id=user.id,
        chunking_strategy=default_chunking,
        embedding_model=default_embedding_config,
    )
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)
    return db_kb

# --- UPDATE ---
def update_kb(db: Session, db_kb: KnowledgeBase, kb_in: KnowledgeBaseUpdate) -> KnowledgeBase:
    update_data = kb_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_kb, field, value)
    
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)
    return db_kb

def update_kb_config(db: Session, db_kb: KnowledgeBase, config_in: KnowledgeBaseConfigUpdate) -> KnowledgeBase:
    if config_in.embedding_model:
        current_config = db_kb.embedding_model or {}
        if isinstance(current_config, str):
            current_config = json.loads(current_config)
        updated_config = config_in.embedding_model.model_dump(exclude_unset=True)
        merged_config = {**current_config, **updated_config}
        db_kb.embedding_model = merged_config
            
    if config_in.chunking_strategy:
        db_kb.chunking_strategy = config_in.chunking_strategy.model_dump()
        
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)
    return db_kb

# --- DELETE ---
def delete_kb(db: Session, db_kb: KnowledgeBase) -> KnowledgeBase:
    for doc in db_kb.documents:
        minio_client.delete_file(doc.file_path_in_minio)
    
    db.delete(db_kb)
    db.commit()
    return db_kb