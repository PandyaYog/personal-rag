from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1 import deps
from app.db.models.user import User
from app.schemas.chunks import Chunk, ChunkUpdate
from app.services import chunk_service

router = APIRouter()

@router.put("/chunks/{chunk_id}", response_model=Chunk)
def update_chunk(
    chunk_id: str,
    chunk_in: ChunkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update the content of a specific chunk. This will trigger re-embedding.
    """
    try:
        updated_point = chunk_service.update_chunk_content(db, chunk_id, chunk_in, current_user)
        response_data = {"id": updated_point.id, **updated_point.payload}
        return Chunk.model_validate(response_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))