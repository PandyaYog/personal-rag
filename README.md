# Personal RAG System (Built from Scratch)

**A transparent, educational implementation of Retrieval-Augmented Generation without the "magic" of heavy frameworks.**

## 💡 The Philosophy: Why "From Scratch"?

In the rapidly evolving world of AI, libraries like LangChain and LlamaIndex have become the go-to solutions for building RAG applications. While these frameworks are incredibly powerful, they often abstract away the critical mechanics of the system.

**I chose not to use them for this project.**

Why? Because to truly master RAG, you need to understand the pipeline at a bare-metal level. You need to see exactly how:
*   A PDF is parsed and cleaned.
*   Text is split into meaningful chunks (and why the chunking strategy matters).
*   Embeddings are generated and stored.
*   Vector search retrieves the *right* context.
*   That context is injected into the LLM's prompt.

This project is designed to be a clear, readable reference implementation. It exposes the internal plumbing of a RAG system, giving you full control and visibility into every step of the process.

## 🚀 What is this Project?

This is a full-stack RAG application designed to let you build your own knowledge base and chat with it.

**Key Features:**
*   **Document Ingestion:** Upload PDF documents which are processed asynchronously.
*   **Vector Storage:** Efficient storage and retrieval of high-dimensional text embeddings.
*   **Context-Aware Chat:** Ask questions and get answers grounded in your uploaded documents.
*   **Transparent Pipeline:** Every logic step is written in Python, easy to debug and modify.

## 🛠️ Tech Stack

*   **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) - High-performance, easy-to-learn API framework.
*   **Asynchronous Processing:** [Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/) - Handles heavy document parsing tasks in the background to keep the API responsive.
*   **Vector Database:** [Qdrant](https://qdrant.tech/) - A powerful, open-source vector search engine.
*   **Object Storage:** [MinIO](https://min.io/) - S3-compatible storage for raw document files.
*   **Database:** [PostgreSQL](https://www.postgresql.org/) - Robust relational database for application metadata.
*   **AI/ML:**
    *   **LLM:** [Groq](https://groq.com/) (Llama 3) - For ultra-fast inference speeds.
    *   **Embeddings:** `sentence-transformers` / `fastembed` - Efficient local embedding generation.

## 🧠 Architecture

Here is the high-level data flow of the system:

```mermaid
graph TD
    subgraph "User Interaction"
        User[User]
        API[FastAPI Backend]
    end

    subgraph "Data Storage"
        MinIO[MinIO Object Storage]
        PG[PostgreSQL DB]
        Qdrant[Qdrant Vector DB]
    end

    subgraph "Async Processing"
        Redis[Redis Queue]
        Worker[Celery Worker]
        Embed[Embedding Model]
    end

    subgraph "AI Inference"
        LLM[Groq API (Llama 3)]
    end

    %% Ingestion Flow
    User -- Upload PDF --> API
    API -- Store File --> MinIO
    API -- Save Metadata --> PG
    API -- Enqueue Task --> Redis
    Redis -- Trigger --> Worker
    Worker -- Fetch File --> MinIO
    Worker -- Chunk Text --> Embed
    Embed -- Generate Vectors --> Qdrant

    %% Chat Flow
    User -- Ask Question --> API
    API -- Embed Query --> Embed
    Embed -- Vector Search --> Qdrant
    Qdrant -- Return Context --> API
    API -- Construct Prompt --> LLM
    LLM -- Generate Answer --> API
    API -- Response --> User
```

## ⚙️ Setup & Installation

### Prerequisites
*   Python 3.10+
*   Docker & Docker Compose

### 1. Clone the Repository
```bash
git clone <repository-url>
cd personal-rag-system
```

### 2. Environment Configuration
Create a `.env` file in the root directory. You can use the provided example as a template:
```bash
cp .env.example .env
```
**Important:** You will need a [Groq API Key](https://console.groq.com/) to run the LLM. Add it to your `.env` file.

### 3. Start Infrastructure
Spin up the required services (Postgres, Qdrant, Redis, MinIO) using Docker Compose:
```bash
docker-compose up -d
```

### 4. Install Dependencies
It is recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
```

### 5. Database Migrations
Initialize the database schema:
```bash
alembic upgrade head
```

### 6. Run the Application
Start the FastAPI server:
```bash
uvicorn main:app --reload
```

### 7. Run the Background Worker
In a separate terminal, start the Celery worker to handle document processing:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

## � Detailed Documentation

This project is designed to be educational. I have written detailed guides explaining every component of the RAG pipeline:

*   **[User Guide](docs/USER_GUIDE.md):** Start here! A step-by-step guide on how to use the app (Knowledge Bases -> Assistants -> Chats).
*   **[Chunking Strategies](docs/CHUNKING_STRATEGIES.md):** Learn about the 7 different ways to split text (Fixed, Semantic, Hybrid, etc.).
*   **[Retrieval Strategies](docs/RETRIEVAL_STRATEGIES.md):** Understand the 8 search methods (Dense, Sparse, RRF, Multi-Vector).
*   **[Embedding Models](docs/EMBEDDING_MODELS.md):** A deep dive into Vector Embeddings and Qdrant configuration.
*   **[Parsing Strategies](docs/PARSING_STRATEGIES.md):** How we handle PDFs, DOCX, and other file formats.
*   **[Testing APIs](docs/TESTING_APIS.md):** How to use the built-in debugging tools to inspect the pipeline.

## 🚧 Status & Contributions

**Current Status:**
This project is a robust proof-of-concept designed for educational clarity. While the core functionality is implemented and fully operational, software is rarely "finished." I am actively refining the codebase, optimizing performance, and expanding test coverage.

**Frontend:**
The backend is the heart of this repository. A modern React-based frontend is currently under active development and will be integrated soon to provide a complete user experience.

**Contributions:**
I welcome contributions! Whether it's fixing a bug, improving the documentation, or suggesting a new feature, feel free to open an issue or submit a pull request. Let's learn and build together.
