import uuid
from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Integer, JSON,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledgebases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    avatar = Column(String, nullable=True) 
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User")
    documents = relationship("Document", back_populates="kb", cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    chunking_strategy = Column(JSON, nullable=False)
    embedding_model = Column(JSON, nullable=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    file_path_in_minio = Column(String, nullable=False, unique=True)
    file_size = Column(Integer, nullable=False) 
    file_extension = Column(String, nullable=False)
    num_chunks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    processing_status = Column(String, default="PENDING", nullable=False)
    kb_id = Column(UUID(as_uuid=True), ForeignKey("knowledgebases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    kb = relationship("KnowledgeBase", back_populates="documents")
    uploader = relationship("User")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())