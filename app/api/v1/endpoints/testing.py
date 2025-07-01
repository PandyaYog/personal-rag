from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1 import deps
from app.db.models.user import User
from app.schemas.testing import (
    ChunkingTestRequest, 
    ChunkingTestResponse,
    RetrievalTestRequest,
    RetrievalTestResponse
)
from app.services import testing_service

router = APIRouter()

@router.post(
    "/chunking", 
    response_model=ChunkingTestResponse,
    summary="Test a Chunking Strategy",
    description="Provides a stateless endpoint to test how a given text would be chunked using a specific strategy and parameters."
)
def test_chunking(request: ChunkingTestRequest, current_user: User = Depends(deps.get_current_active_user)):
    """
    Tests a chunking strategy on provided text content.
    This endpoint is public and does not require authentication as it does not interact with any stored data.
    """
    try:
        result = testing_service.test_chunking_strategy(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during chunking: {e}"
        )


@router.post(
    "/retrieval", 
    response_model=RetrievalTestResponse,
    summary="Test a Retrieval Strategy",
    description="Tests a retrieval strategy for a given query against a user's specified knowledge bases."
)
def test_retrieval(
    request: RetrievalTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Tests a retrieval strategy by searching within the authenticated user's knowledge bases.
    Requires authentication.
    """
    try:
        results = testing_service.test_retrieval_strategy(db, request, current_user)
        return {"retrieved_chunks": results}
    except NotImplementedError as e:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during retrieval: {e}"
        )