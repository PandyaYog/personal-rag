# 🧭 User Guide: How the App Works

This application is more than just a simple "Chat with PDF" tool. It is a professional **Knowledge Management System** designed to bridge the gap between your raw data (files) and actionable intelligence (answers).

To use it effectively, you need to understand the three core concepts: **Knowledge Bases**, **Assistants**, and **Chats**.

---

## 1. The Core Concepts (The Hierarchy)

Think of this system like a real-world library, but supercharged with AI:

1.  **📚 Knowledge Base (The Library Shelf):**
    *   **Role:** The Storage Layer.
    *   This is where you store your documents. It handles the "heavy lifting" of converting text into mathematical vectors.
    *   It is *passive*. It doesn't "think"; it just remembers.
    *   *Example:* "Legal Documents", "Personal Journals", "Python Textbooks".

2.  **🤖 Assistant (The Librarian):**
    *   **Role:** The Logic Layer.
    *   This is the "Brain". It has a personality, instructions, and a memory of your conversation.
    *   Crucially, **an Assistant must be assigned to a Knowledge Base**. Without a KB, the Assistant is just a generic chatbot (like standard ChatGPT) with no access to your private data.
    *   *Example:* "Legal Advisor" (linked to Legal Docs), "Coding Tutor" (linked to Python Textbooks).

3.  **💬 Chat (The Conversation):**
    *   **Role:** The Interaction Layer.
    *   This is a specific session between YOU and an ASSISTANT.
    *   You can have multiple chats with the same assistant (e.g., "Session 1: Contract Review", "Session 2: Lease Agreement"). The Assistant remembers the context *within* a chat, but not *across* chats.

---

## 2. The Workflow: Step-by-Step

Follow this flow to build your first RAG application.

### Step 1: Create a Knowledge Base
*   **Action:** Go to the "Knowledge Bases" tab and click "Create New".
*   **Why?** You need a container for your data.
*   **Behind the Scenes:** The system contacts the **Qdrant Vector Database** and creates a new "Collection". Think of this as creating a new, empty bucket specifically designed to hold high-dimensional vectors (numbers).

### Step 2: Ingest Documents
*   **Action:** Open your new Knowledge Base and upload files (PDFs, Text, etc.).
*   **Why?** The system needs to read, understand, and index your content.
*   **What happens (The "Magic"):**
    1.  **Parsing:** The file is cleaned and converted to text (see `PARSING_STRATEGIES.md`).
    2.  **Chunking:** The text is intelligently split into small, meaningful pieces (see `CHUNKING_STRATEGIES.md`).
    3.  **Embedding:** Each piece is run through an AI model to create a "vector" (see `EMBEDDING_MODELS.md`).
    *   *Note:* This process is CPU-intensive. A large PDF might take a minute to process because the AI is reading every sentence carefully.

### Step 3: Create an Assistant
*   **Action:** Go to the "Assistants" tab and click "Create New".
*   **Why?** You need an interface to talk to your data.
*   **Crucial Settings:**
    *   **Knowledge Base:** You MUST link the KB you created in Step 1.
    *   **System Prompt:** This is where you program the AI's behavior.
        *   *Bad Prompt:* "You are a bot."
        *   *Good Prompt:* "You are a senior legal analyst. Answer strictly based on the provided documents. If the answer is not in the text, say 'I don't know'."
    *   **Temperature:** Controls creativity.
        *   `0.0` (Strict): Good for factual Q&A.
        *   `0.7` (Creative): Good for brainstorming or writing.

### Step 4: Start a Chat
*   **Action:** Go to the "Chats" tab, select your "Finance Guru" assistant, and start a new chat.
*   **Why?** To begin the Q&A loop.
*   **The RAG Loop (What actually happens):**
    1.  **Query:** You ask, "What is the refund policy?"
    2.  **Retrieval:** The system pauses, searches your Knowledge Base for the top 5 chunks related to "refunds" (using the strategies in `RETRIEVAL_STRATEGIES.md`).
    3.  **Context Injection:** It secretly pastes those 5 chunks into the prompt, right before your question.
    4.  **Generation:** The LLM reads the chunks and generates an answer based *only* on that information.

---

## 3. Why this Architecture?

Why separate "Assistants" from "Knowledge Bases"? Why not just upload a file and chat?

**1. The Power of Reusability (One-to-Many)**
Imagine you have a huge Knowledge Base called **"Company Financial Reports"** (100+ PDFs). Indexing this takes time and storage. You can create **multiple assistants** that use this *same* data for different purposes:
*   **Assistant A ("The Auditor"):** Strict, low temperature, looks for errors.
*   **Assistant B ("The Summarizer"):** Creative, high temperature, writes blog posts.
*   **Assistant C ("The Historian"):** Focuses on year-over-year trends.
All three use the same expensive vector index.

**2. Data Safety**
If you delete an Assistant (e.g., "The Auditor"), **you do not delete the data**. Your Knowledge Base remains intact. This prevents accidental data loss and allows you to experiment with different Assistant personalities without re-uploading files.
