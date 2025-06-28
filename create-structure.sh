#!/bin/bash

# This script sets up the project structure for the RAG from Scratch application.

echo "Creating project directories..."

# Main application directory
mkdir -p app/api/v1/endpoints
mkdir -p app/core
mkdir -p app/db/models
mkdir -p app/db/migrations
mkdir -p app/rag/chunking
mkdir -p app/rag/embedding
mkdir -p app/rag/retrieval
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/tasks
mkdir -p app/utils
mkdir -p tests

echo "Creating initial Python files..."

# Create __init__.py files to make directories Python packages
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/db/__init__.py
touch app/db/models/__init__.py
touch app/rag/__init__.py
touch app/rag/chunking/__init__.py
touch app/rag/embedding/__init__.py
touch app/rag/retrieval/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/tasks/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py

# Create endpoint files
touch app/api/v1/endpoints/auth.py
touch app/api/v1/endpoints/users.py
touch app/api/v1/endpoints/knowledgebases.py
touch app/api/v1/endpoints/documents.py
touch app/api/v1/endpoints/assistants.py
touch app/api/v1/endpoints/chats.py
touch app/api/v1/deps.py

# Create core files
touch app/core/config.py
touch app/core/celery_app.py

# Create database files
touch app/db/session.py
touch app/db/models/user.py
touch app/db/models/knowledgebase.py
# You can add more model files here as needed

# Create RAG logic placeholders
touch app/rag/chunking/base.py
touch app/rag/chunking/methods.py
touch app/rag/embedding/base.py
touch app/rag/embedding/models.py
touch app/rag/retrieval/base.py
touch app/rag/retrieval/search.py

# Create Pydantic schema files
touch app/schemas/user.py
touch app/schemas/token.py
touch app/schemas/knowledgebase.py
touch app/schemas/document.py
touch app/schemas/assistant.py
touch app/schemas/chat.py

# Create service layer files
touch app/services/user_service.py
touch app/services/kb_service.py
touch app/services/document_service.py
touch app/services/assistant_service.py
touch app/services/chat_service.py

# Create Celery task files
touch app/tasks/process_document.py

# Create utility files
touch app/utils/security.py

# Create root level files
touch main.py
touch .env
touch requirements.txt
touch README.md

# Create .gitignore
echo "Creating .gitignore file..."
cat <<EOL > .gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.pytest_cache/
.hypothesis/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak
venv.bak

# IDE files
.idea/
.vscode/

# mypy
.mypy_cache/

# DB files
*.db
*.sqlite3

# Celery
celerybeat-schedule.*
EOL

echo "Project structure created successfully!"