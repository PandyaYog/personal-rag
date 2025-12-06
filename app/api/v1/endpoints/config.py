from fastapi import APIRouter
from model_list import models_embedding, models_semantic_splitting, models_token_splitting, supported_file_type, split_differently

router = APIRouter()

@router.get("/models")
def get_model_config():
    """
    Returns the list of available models and supported file types.
    """
    return {
        "models_embedding": models_embedding,
        "models_semantic_splitting": models_semantic_splitting,
        "models_token_splitting": models_token_splitting,
        "supported_file_types": supported_file_type,
        "split_differently": split_differently
    }
