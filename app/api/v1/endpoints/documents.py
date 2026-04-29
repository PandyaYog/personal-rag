import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1 import deps
from app.db.models.user import User
from app.schemas import document as doc_schema
from app.schemas.chunks import Chunk, ChunkCreate
from app.services import document_service, kb_service, minio_service
from app.services.qdrant_service import qdrant_service
import asyncio
from functools import partial

router = APIRouter()

@router.post("/{kb_id}/documents/upload", response_model=doc_schema.Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Upload a document to a specific Knowledge Base.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")
        
    loop = asyncio.get_running_loop()
    doc = await loop.run_in_executor(
        None,
        partial(document_service.upload_document, db=db, file=file, kb=db_kb, user=current_user)
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload document to storage.")
        
    return doc

@router.get("/{kb_id}/documents", response_model=List[doc_schema.Document])
def list_documents(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    List all documents within a specific Knowledge Base.
    """
    db_kb = kb_service.get_kb_by_id(db, kb_id=kb_id, user_id=current_user.id)
    if not db_kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")

    docs = document_service.get_all_docs_in_kb(db, kb_id=kb_id, user_id=current_user.id, skip=skip, limit=limit)
    return docs

@router.get("/{kb_id}/documents/{doc_id}", response_model=doc_schema.Document)
def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get details of a specific document.
    """
    doc = document_service.get_doc_by_id(db, doc_id=doc_id, user_id=current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.put("/{kb_id}/documents/{doc_id}", response_model=doc_schema.Document)
def update_document(
    doc_id: uuid.UUID,
    doc_in: doc_schema.DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Update a document's details (e.g., name, active status).
    """
    db_doc = document_service.get_doc_by_id(db, doc_id=doc_id, user_id=current_user.id)
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    return document_service.update_document(db, db_doc=db_doc, doc_in=doc_in)

@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Delete a document from a Knowledge Base.
    """
    db_doc = document_service.get_doc_by_id(db, doc_id=doc_id, user_id=current_user.id)
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    document_service.delete_document(db, db_doc=db_doc)
    return None

@router.get("/{kb_id}/documents/{doc_id}/download")
async def download_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Download the original document file.
    """
    db_doc = document_service.get_doc_by_id(db, doc_id=doc_id, user_id=current_user.id)
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    def _download_and_read():
        return minio_service.minio_client.get_object_file(db_doc.file_path_in_minio)

    loop = asyncio.get_running_loop()
    file_content = await loop.run_in_executor(None, _download_and_read)
    
    if file_content is None:
        raise HTTPException(status_code=500, detail="Could not retrieve file from storage")

    return Response(file_content, media_type='application/octet-stream', headers={"Content-Disposition": f"attachment; filename={db_doc.name}"})


@router.post("/{kb_id}/documents/{doc_id}/process", response_model=doc_schema.DocumentStatus)
async def trigger_document_reprocessing(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Manually re-trigger the chunking and embedding process for a document.
    Useful if the KB's configuration has changed.
    """
    db_doc = document_service.get_doc_by_id(db, doc_id=doc_id, user_id=current_user.id)
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if db_doc.processing_status == "PROCESSING":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is already being processed.")

    loop = asyncio.get_running_loop()
    reprocessed_doc = await loop.run_in_executor(
        None,
        partial(document_service.reprocess_document, db, db_doc=db_doc)
    )
    return doc_schema.DocumentStatus.model_validate(reprocessed_doc)

@router.get("/{kb_id}/documents/{doc_id}/chunks", response_model=List[Chunk])
def get_document_chunks(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get all chunks for a specific document.
    """
    doc = document_service.get_doc_by_id(db, doc_id=doc_id, user_id=current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    points = qdrant_service.get_chunks_for_document(str(doc_id))
    chunks = [{"id": point.id, **point.payload} for point in points]
    return chunks

@router.post("/{kb_id}/documents/{doc_id}/chunks", response_model=Chunk, status_code=status.HTTP_201_CREATED)
async def add_chunk_to_document(
    doc_id: uuid.UUID,
    chunk_in: ChunkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Manually add a new chunk to a document.
    """
    try:
        loop = asyncio.get_running_loop()
        new_point = await loop.run_in_executor(
            None,
            partial(document_service.add_manual_chunk, db, doc_id, chunk_in, current_user)
        )
        response_data = {"id": new_point.id, **new_point.payload}
        return Chunk.model_validate(response_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))