import uuid
from pydantic import BaseModel, Field

class Chunk(BaseModel):
    id: str = Field(..., description="The Qdrant point ID for the chunk.")
    doc_id: uuid.UUID
    chunk_num: int
    content: str = Field(..., alias="chunk_content")

    class Config:
        from_attributes = True
        populate_by_name = True 

class ChunkUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="The new text content for the chunk.")

class ChunkCreate(BaseModel):
    content: str = Field(..., min_length=1, description="The text content for the new chunk.")