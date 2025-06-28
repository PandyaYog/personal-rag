import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class DocumentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="project_proposal.pdf")

class DocumentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None

class Document(DocumentBase):
    id: uuid.UUID
    kb_id: uuid.UUID
    file_path_in_minio: str
    file_size: int 
    file_extension: str
    num_chunks: int
    is_active: bool
    processing_status: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True

class DocumentStatus(BaseModel):
    id: uuid.UUID
    name: str
    processing_status: str