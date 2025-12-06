# 🧩 Chunking Strategies Explained

## What is "Chunking" and Why Do We Need It?

Imagine trying to study a 500-page textbook. You wouldn't try to memorize the entire book in one glance. Instead, you break it down into chapters, paragraphs, or sentences to understand it piece by piece.

**Chunking** is exactly that process for AI.

When we build a RAG system, we can't just feed a whole PDF into the AI's brain (it's too big and expensive). We have to cut the document into smaller, manageable pieces called "chunks."

### The "Goldilocks" Problem
Getting the size of these chunks right is the hardest part of RAG:
*   **Too Small:** The AI sees a sentence like *"He did it."* but doesn't know *who* "he" is or *what* he did. The context is lost.
*   **Too Big:** The AI gets 10 pages of text when it only needed one specific fact. It gets confused by the "noise" and might miss the answer.
*   **Just Right:** The chunk contains a complete thought or idea, giving the AI exactly what it needs to answer the question.

This project implements **7 distinct strategies** to help you find that "Just Right" balance for your specific documents.

---

## 1. Fixed Size Chunking (`FixedSizeChunker`)

### 🔍 What is it?
The "Ruler" method. It ignores the content and simply cuts the text every X characters.

### ⚙️ How it works
Imagine taking a pair of scissors and cutting a long scroll of paper every 10 inches, regardless of what is written on it.
*   **Chunk Size:** The length of the cut (e.g., 1000 characters).
*   **Overlap:** To prevent cutting a word in half at the edge, we repeat the last 100 characters of chunk #1 at the beginning of chunk #2. It's like repeating the last sentence of the previous page on the top of the next page so you don't lose the thread.

### 🎛️ Parameters
*   `chunk_size` (int): Number of characters per chunk.
*   `chunk_overlap` (int): Number of characters to overlap.

### 💡 Why use it?
*   **Pros:** Extremely fast and simple.
*   **Cons:** It's "dumb." It might cut a sentence right in the middle, making it hard for the AI to understand.

---

## 2. Sentence Based Chunking (`SentenceBasedChunker`)

### 🔍 What is it?
The "Grammar" method. It respects the rules of language.

### ⚙️ How it works
Instead of counting characters, it looks for full stops (`.`), question marks (`?`), and exclamation points (`!`). It groups full sentences together until they reach the size limit.
*   **Analogy:** It's like reading a book and stopping only when you finish a full sentence. You never stop in the middle of a word.

### 🎛️ Parameters
*   `max_chunk_size` (int): The maximum character limit. If a sentence pushes the chunk over this limit, a new chunk is started.

### 💡 Why use it?
*   **Pros:** Guarantees that every chunk contains complete, grammatically correct sentences.
*   **Cons:** If you have a very long paragraph with many sentences, it might still get split in the middle of the paragraph, losing the broader context.

---

## 3. Recursive Character Chunking (`RecursiveCharacterChunker`)

### 🔍 What is it?
The "Smart Splitter" (and the industry standard). It tries to keep related text together.

### ⚙️ How it works
It follows a hierarchy of rules, trying to be as gentle as possible:
1.  **Try Paragraphs:** First, it tries to split by double newlines (`\n\n`). This keeps whole paragraphs together.
2.  **Try Sentences:** If a paragraph is still too big, it splits by single newlines or periods (`.`).
3.  **Try Words:** If a sentence is somehow massive, only then does it split by spaces.

### 🎛️ Parameters
*   `chunk_size` (int): Target size for chunks.
*   `chunk_overlap` (int): Overlap to preserve context.
*   `separators` (list): The hierarchy of split characters (default: `["\n\n", "\n", ". ", " ", ""]`).

### 💡 Why use it?
*   **Pros:** It respects the natural structure of the document. It keeps paragraphs intact whenever possible, which usually means keeping a single "idea" intact.
*   **Cons:** Slightly slower than the "Ruler" method, but worth it for the quality.

---

## 4. Sliding Window Chunking (`SlidingWindowChunker`)

### 🔍 What is it?
The "Moving Camera" method. It captures overlapping "scenes" of text.

### ⚙️ How it works
Imagine a camera panning across a long painting.
*   **Shot 1:** Captures the left side.
*   **Shot 2:** Moves slightly to the right, but still includes the middle part of Shot 1.
*   **Result:** The middle part is photographed twice. This redundancy ensures that if the "answer" lies on the boundary, it is fully captured in at least one shot.

### 🎛️ Parameters
*   `window_size` (int): The size of the "camera frame" (chunk).
*   `step_size` (int): How far the camera moves forward for the next shot.
*   `unit` (str): Can be `'char'`, `'word'`, or `'sentence'`.

### 💡 Why use it?
*   **Pros:** The safest method for deep analysis. You never miss context at the edges.
*   **Cons:** **High Redundancy.** You store the same text multiple times, which increases storage costs and search time.

---

## 5. Token Based Chunking (`TokenBasedChunker`)

### 🔍 What is it?
The "Translator's" method. It counts in the AI's native language.

### ⚙️ How it works
Computers don't read words like "Apple"; they read numbers called **Tokens**.
*   "Apple" might be 1 token.
*   "Ingenious" might be 3 tokens.
This method converts text into tokens *first*, counts them, and cuts exactly at the limit (e.g., 512 tokens).

### 🎛️ Parameters
*   `token_size` (int): Max tokens per chunk.
*   `model_name` (str): The specific vocabulary to use (e.g., `cl100k_base` for GPT-4).

### 💡 Why use it?
*   **Pros:** **Technical Safety.** LLMs have strict limits (e.g., 8192 tokens). This guarantees you never accidentally send too much text, preventing API errors.
*   **Cons:** Slower because it has to translate text-to-numbers and back.

---

## 6. Semantic Chunking (`SemanticChunker`)

### 🔍 What is it?
The "Topic Detector". It uses AI to understand the *meaning* of the text, not just the grammar.

### ⚙️ How it works
Imagine you are reading a magazine. You know a new article starts not because of a specific punctuation mark, but because the **topic changes**.
1.  It calculates the "similarity score" between every pair of sentences.
2.  If Sentence A is about "Cats" and Sentence B is about "Dogs", the score drops.
3.  When the score drops below a certain threshold (the "breakpoint"), it makes a cut.

### 🎛️ Parameters
*   `embedding_model` (str): The AI brain used to judge similarity (e.g., `all-MiniLM-L6-v2`).
*   `breakpoint_percentile` (int): The sensitivity. Higher = fewer, larger chunks (only cuts on big topic shifts).
*   `backend` (str): `sentence_transformers` or `fastembed`.

### 💡 Why use it?
*   **Pros:** Creates the most coherent chunks. Each chunk represents a distinct idea or topic, which is perfect for retrieval.
*   **Cons:** Slower and more expensive because it has to run an AI model *during* the chunking process.

---

## 7. Hybrid Chunking (`HybridChunker`) - 🏆 Recommended

### 🔍 What is it?
The "Safety Net". It combines the smarts of Semantic Chunking with the safety of Token Chunking.

### ⚙️ How it works
1.  **Step 1 (The Smart Way):** It tries to split the document by topic using **Semantic Chunking**.
2.  **Step 2 (The Safety Check):** It measures the size of each topic.
3.  **Step 3 (The Backup Plan):** If a specific topic is too long for the AI (e.g., a 10-page history of Rome), it uses **Token Chunking** to sub-divide that specific part into smaller, safe pieces.

### 💡 Why use it?
This is the default strategy in this project. It offers the best of both worlds:
*   It respects the semantic structure of the document (like Semantic Chunking).
*   It guarantees technical compatibility with the LLM (like Token Chunking).

While no single strategy is perfect for every document, **Hybrid Chunking** is the most robust starting point for a general-purpose RAG system. It balances human-like understanding with machine-like safety.

### 🏁 Conclusion: The "No Free Lunch" Theorem in Chunking

While **Hybrid Chunking** is the default recommendation for this project, it is crucial to understand that **there is no single "best" strategy for all scenarios.** The optimal choice depends heavily on two factors:

1.  **Your Data:**
    *   **Structured Data (Code, JSON, Logs):** Semantic chunking often fails here because the "meaning" isn't narrative. *Token-based* or *Recursive* chunking usually works better.
    *   **Narrative Text (Books, Articles):** *Semantic* and *Hybrid* strategies shine because they respect the flow of ideas.
    *   **Short Snippets (Tweets, Reviews):** *Fixed-size* might be sufficient and faster.

2.  **Your RAG Application:**
    *   **Q&A System:** Needs precise, self-contained chunks (Hybrid/Semantic).
    *   **Summarization:** Needs broad context, potentially tolerating larger, less precise chunks (Recursive/Sliding Window).

**Why Hybrid Shines (Most of the time):**
It balances the *quality* of semantic understanding with the *safety* of token limits. It attempts to capture complete thoughts but has a fallback mechanism to prevent technical errors when those thoughts are too long.

**However**, if you are building a specialized system (e.g., a RAG for Python codebases), you might find that a simpler `RecursiveCharacterChunker` with custom separators performs significantly better than the heavy-duty Hybrid approach. Always test multiple strategies against your specific dataset!
