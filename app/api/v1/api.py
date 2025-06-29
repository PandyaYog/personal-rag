from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, knowledgebases, documents, assistants, chats

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(knowledgebases.router, prefix="/knowledgebases", tags=["Knowledge Bases"])
api_router.include_router(documents.router, prefix="/knowledgebases", tags=["Documents"])
api_router.include_router(assistants.router, prefix="/assistants", tags=["Assistants"])
api_router.include_router(chats.router, prefix="", tags=["Chats"])