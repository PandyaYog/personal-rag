import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1 import deps
from app.db.models.user import User
from app.schemas.assistant import Assistant, AssistantCreate, AssistantUpdate, LinkedKnowledgeBase
from app.services import assistant_service

router = APIRouter()

@router.post("/", response_model=Assistant, status_code=status.HTTP_201_CREATED)
def create_assistant(
    assistant_in: AssistantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    try:
        return assistant_service.create_assistant(db, assistant_in, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
@router.get("/", response_model=List[Assistant])
def list_assistants(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    assistants = assistant_service.get_all_assistants_for_user(db, user_id=current_user.id)
    response = []
    for ass in assistants:
        ass_data = Assistant.model_validate(ass)
        ass_data.num_chats = len(ass.chats)
        response.append(ass_data)
    return response

@router.get("/{assistant_id}", response_model=Assistant)
def get_assistant(
    assistant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    ass = assistant_service.get_assistant_by_id(db, assistant_id, current_user.id)
    if not ass:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    ass_data = Assistant.model_validate(ass)
    ass_data.num_chats = len(ass.chats)
    return ass_data

@router.put("/{assistant_id}", response_model=Assistant)
def update_assistant(
    assistant_id: uuid.UUID,
    assistant_in: AssistantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    db_ass = assistant_service.get_assistant_by_id(db, assistant_id, current_user.id)
    if not db_ass:
        raise HTTPException(status_code=404, detail="Assistant not found")
    try:
        return assistant_service.update_assistant(db, db_ass, assistant_in, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assistant(
    assistant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    db_ass = assistant_service.get_assistant_by_id(db, assistant_id, current_user.id)
    if not db_ass:
        raise HTTPException(status_code=404, detail="Assistant not found")
    assistant_service.delete_assistant(db, db_ass)
    return None