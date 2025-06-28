from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# This import will be added later when we create the routers
# from app.api.v1.api import api_router 

app = FastAPI(
    title="RAG from Scratch API",
    description="An API for a custom-built Retrieval-Augmented Generation system.",
    version="0.1.0"
)

# Set up CORS middleware
# This is crucial for allowing frontend applications to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Placeholder for the API router
# app.include_router(api_router, prefix="/v1")

@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint for health checks.
    """
    return {"status": "ok", "message": "Welcome to the RAG from Scratch API!"}