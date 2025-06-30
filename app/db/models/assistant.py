import uuid
from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Text, JSON, Table,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base

assistant_knowledgebase_association = Table(
    'assistant_knowledgebase',
    Base.metadata,
    Column('assistant_id', UUID(as_uuid=True), ForeignKey('assistants.id'), primary_key=True),
    Column('knowledgebase_id', UUID(as_uuid=True), ForeignKey('knowledgebases.id'), primary_key=True)
)

class Assistant(Base):
    __tablename__ = "assistants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    llm_config = Column(JSON, nullable=False)
    embedding_config = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner = relationship("User")
    chats = relationship("Chat", back_populates="assistant", cascade="all, delete-orphan")
    knowledge_bases = relationship(
        "KnowledgeBase",
        secondary=assistant_knowledgebase_association,
        backref="assistants"
    )

class Chat(Base):
    __tablename__ = "chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False, default="New Chat")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assistant_id = Column(UUID(as_uuid=True), ForeignKey("assistants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner = relationship("User")
    assistant = relationship("Assistant", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    role = Column(String, nullable=False)
    content = Column(JSONB, nullable=False)
    is_good = Column(Boolean, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat = relationship("Chat", back_populates="messages")
    parent = relationship("Message", remote_side=[id], backref="children")