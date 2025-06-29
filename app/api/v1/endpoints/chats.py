import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1 import deps
from app.db.models.user import User
from app.db.models.assistant import Chat
from app.schemas.chat import Chat as ChatSchema, ChatCreate, ChatWithHistory, UserQuery, Message as MessageSchema
from app.services import assistant_service, chat_service

router = APIRouter()

@router.post("/assistants/{assistant_id}/chats", response_model=ChatSchema, status_code=status.HTTP_201_CREATED)
def create_chat(
    assistant_id: uuid.UUID,
    chat_in: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    assistant = assistant_service.get_assistant_by_id(db, assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    chat = Chat(
        name=chat_in.name if chat_in.name else "New Chat",
        user_id=current_user.id,
        assistant_id=assistant_id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

@router.get("/assistants/{assistant_id}/chats/{chat_id}", response_model=ChatWithHistory)
def get_chat_history(
    chat_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.post("/assistants/{assistant_id}/chats/{chat_id}/query", response_model=MessageSchema)
def query_chat(
    chat_id: uuid.UUID,
    query_in: UserQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    try:
        return chat_service.handle_user_query(db, query_in, chat_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")