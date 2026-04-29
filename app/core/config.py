import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- PostgreSQL Configuration ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # --- Minio Configuration ---
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str

    # --- Redis Configuration ---
    REDIS_HOST: str
    REDIS_PORT: int

    # --- Qdrant Configuration ---
    QDRANT_HOST: str
    QDRANT_PORT: int

    # --- FastAPI Application ---
    APP_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:5173"
    
    # --- LLM Provider (Groq) ---
    GROQ_API_KEY: str

    # --- Embedding Service ---
    EMBEDDING_SERVICE_URL: str = "http://embedding_service:8000"

    # --- Email Configuration (fastapi-mail) ---
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = ""
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()