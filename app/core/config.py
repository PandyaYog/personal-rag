import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- PostgreSQL Configuration (Neon) ---
    DATABASE_URL: str

    # --- Storage Configuration (Cloudflare R2) ---
    R2_ENDPOINT: str
    R2_ACCESS_KEY: str
    R2_SECRET_KEY: str
    R2_BUCKET_NAME: str

    # --- Redis Configuration (Upstash) ---
    REDIS_URL: str

    # --- Qdrant Configuration (Qdrant Cloud) ---
    QDRANT_URL: str
    QDRANT_API_KEY: str

    # --- FastAPI Application ---
    APP_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:5173"
    
    # --- LLM Provider (Groq) ---
    GROQ_API_KEY: str

    # --- Embedding Service (Hugging Face Space) ---
    EMBEDDING_SERVICE_URL: str
    EMBEDDING_SERVICE_API_KEY: str

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