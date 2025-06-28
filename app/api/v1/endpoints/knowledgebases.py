import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1 import deps
from app.db.models.user import User
from app.db.models.knowledgebase import KnowledgeBase
from app.schemas import knowledgebase as kb_schema
from app.services import kb_service

router = APIRouter()

@router.post("/", response_model=kb_schema.KnowledgeBase, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    kb_in: kb_schema.KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Create a new Knowledge Base.
    """
    kb = kb_service.create_kb(db=db, kb_in=kb_in, user=current_user)
    return kb_schema.KnowledgeBase.model_validate(kb)


@router.get("/", response_model=List[kb_schema.KnowledgeBase])
def list_knowledge_bases(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    List all Knowledge Bases for the current user.
    """
    kbs_with_counts = kb_service.get_all_kbs_for_user(db, user_id=current_user.id, skip=skip, limit=limit)
    
    response = []
    for kb, num_docs, num_processed in kbs_with_counts:
        kb_data = kb_schema.KnowledgeBase.model_validate(kb)
        kb_data.num_documents = num_docs or 0
        kb_data.num_processed_documents = num_processed or 0
        response.append(kb_data)
        
    return response


@router.get("/{kb_id}", response_model=kb_schema.KnowledgeBase)
def get_knowledge_base(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get details of a specific Knowledge Base.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")
    
    kbs_with_counts = kb_service.get_all_kbs_for_user(db, user_id=current_user.id)
    kb_with_count = next((item for item in kbs_with_counts if item[0].id == kb_id), None)

    if not kb_with_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")

    kb, num_docs, num_processed = kb_with_count
    response = kb_schema.KnowledgeBase.model_validate(kb)
    response.num_documents = num_docs or 0
    response.num_processed_documents = num_processed or 0

    return response


@router.put("/{kb_id}", response_model=kb_schema.KnowledgeBase)
def update_knowledge_base(
    kb_id: uuid.UUID,
    kb_in: kb_schema.KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Update a Knowledge Base's name or description.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")
    
    updated_kb = kb_service.update_kb(db=db, db_kb=db_kb, kb_in=kb_in)
    return updated_kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Delete a Knowledge Base and all its associated documents.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")
    
    kb_service.delete_kb(db=db, db_kb=db_kb)
    return None


@router.get("/{kb_id}/config", response_model=kb_schema.KnowledgeBaseWithConfig)
def get_kb_configuration(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get the advanced configuration of a Knowledge Base.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")
    
    kbs_with_counts = kb_service.get_all_kbs_for_user(db, user_id=current_user.id)
    kb_with_count = next((item for item in kbs_with_counts if item[0].id == kb_id), (None, 0, 0))
    
    response = kb_schema.KnowledgeBaseWithConfig.model_validate(db_kb)
    response.num_documents = kb_with_count[1] or 0
    response.num_processed_documents = kb_with_count[2] or 0
    
    return response


@router.put("/{kb_id}/config", response_model=kb_schema.KnowledgeBaseWithConfig)
def update_kb_configuration(
    kb_id: uuid.UUID,
    config_in: kb_schema.KnowledgeBaseConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Update the advanced configuration of a Knowledge Base.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")
    
    updated_kb = kb_service.update_kb_config(db=db, db_kb=db_kb, config_in=config_in)
    
    return get_kb_configuration(kb_id=updated_kb.id, db=db, current_user=current_user)