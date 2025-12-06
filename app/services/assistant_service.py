import uuid
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.user import User
from app.db.models.assistant import Assistant
from app.db.models.knowledgebase import KnowledgeBase
from app.schemas.assistant import AssistantCreate, AssistantUpdate, LLMConfig
from app.schemas.knowledgebase import EmbeddingModelConfig

def create_assistant(db: Session, assistant_in: AssistantCreate, user: User) -> Assistant:
    """Creates a new assistant and links it to knowledge bases."""
    # Fetch and validate knowledge bases
    linked_kbs = db.query(KnowledgeBase).filter(
        KnowledgeBase.id.in_(assistant_in.knowledge_base_ids),
        KnowledgeBase.user_id == user.id
    ).all()
    if len(linked_kbs) != len(assistant_in.knowledge_base_ids):
        raise ValueError("One or more knowledge base IDs are invalid or do not belong to the user.")

    # Set default configs if not provided
    llm_config_data = assistant_in.llm_config.model_dump() if assistant_in.llm_config else LLMConfig().model_dump()
    embedding_config_data = assistant_in.embedding_config.model_dump() if assistant_in.embedding_config else EmbeddingModelConfig().model_dump()

    db_assistant = Assistant(
        name=assistant_in.name,
        user_id=user.id,
        knowledge_bases=linked_kbs,
        llm_config=llm_config_data,
        embedding_config=embedding_config_data
    )
    db.add(db_assistant)
    db.commit()
    db.refresh(db_assistant)
    return db_assistant

def get_assistant_by_id(db: Session, assistant_id: uuid.UUID, user_id: uuid.UUID) -> Assistant | None:
    return db.query(Assistant).filter(Assistant.id == assistant_id, Assistant.user_id == user_id).first()

def get_all_assistants_for_user(db: Session, user_id: uuid.UUID) -> List[Assistant]:
    return db.query(Assistant).filter(Assistant.user_id == user_id).order_by(desc(Assistant.updated_at)).all()

def update_assistant(db: Session, db_assistant: Assistant, assistant_in: AssistantUpdate, user_id: uuid.UUID) -> Assistant:
    """Updates an assistant's details."""
    update_data = assistant_in.model_dump(exclude_unset=True)
    
    if "name" in update_data:
        db_assistant.name = update_data["name"]
    if "llm_config" in update_data:
        db_assistant.llm_config = update_data["llm_config"]
    if "embedding_config" in update_data:
        db_assistant.embedding_config = update_data["embedding_config"]
    if "knowledge_base_ids" in update_data:
        linked_kbs = db.query(KnowledgeBase).filter(
            KnowledgeBase.id.in_(update_data["knowledge_base_ids"]),
            KnowledgeBase.user_id == user_id
        ).all()
        if len(linked_kbs) != len(update_data["knowledge_base_ids"]):
            raise ValueError("Invalid knowledge base ID provided in update.")
        db_assistant.knowledge_bases = linked_kbs

    db.add(db_assistant)
    db.commit()
    db.refresh(db_assistant)
    return db_assistant

def delete_assistant(db: Session, db_assistant: Assistant):
    db.delete(db_assistant)
    db.commit()