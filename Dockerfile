FROM python:3.11-slim

# Install system dependencies and supervisor
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    antiword \
    libreoffice \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (mandatory for Hugging Face Spaces)
RUN useradd -m -u 1000 user

WORKDIR /app

# Install Python dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Create necessary cache directories and give permissions to the non-root user
RUN mkdir -p /app/model_cache /.cache/huggingface /.config/matplotlib \
    && chown -R user:user /app /.cache /.config

# Switch to the non-root user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Environment variables to keep caches in writable locations
ENV FASTEMBED_CACHE_DIR=/app/model_cache
ENV HF_HOME=/.cache/huggingface

EXPOSE 7860

# Run supervisor to manage both FastAPI and Celery
CMD ["supervisord", "-c", "/app/supervisord.conf"]
