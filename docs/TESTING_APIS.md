# 🧪 Testing & Debugging APIs

RAG systems can often feel like a "Black Box". You put a PDF in, ask a question, and get an answer. But what happened in between?
*   Did the chunking cut off a key sentence?
*   Did the retrieval find the right paragraph?
*   Is the embedding model actually understanding the difference between "Apple" (fruit) and "Apple" (company)?

To answer these questions, this project includes a dedicated **Testing Suite** exposed via API endpoints. These are not for the end-user chat application, but for **you, the developer**, to inspect, debug, and learn.

---

## 1. The Philosophy: "Glass Box" RAG

The goal of these APIs is to make every step of the pipeline **observable**. Instead of guessing why an answer was poor, you can isolate each component:
1.  **Isolate Chunking:** See exactly how text is split before it hits the database.
2.  **Isolate Retrieval:** See exactly what documents are found before they hit the LLM.
3.  **Isolate Embeddings:** Mathematically prove which model works best for your data.

You can access all these endpoints interactively via the **Swagger UI** at `http://localhost:8000/docs`.

---

## 2. Chunking Playground (`/v1/testing/chunking`)

### 🎯 Goal
To answer the question: **"How does the AI actually read my document?"**

AI models cannot read a whole book in one go. They need text broken down into small, bite-sized pieces called "chunks." If you chop the text in the wrong place (e.g., in the middle of a sentence), the AI gets confused. This tool lets you see exactly where the knife cuts.

### ⚙️ How to use
You paste a paragraph of text (e.g., a contract clause) and choose a strategy. The API returns the list of "chunks" exactly as they would be stored in the database.

### 📥 Parameters
*   `text` (string): The raw text you want to test.
*   `strategy_config` (object):
    *   `strategy`: Choose the method (e.g., "fixed_size" for simple cuts, "semantic" for smart cuts based on meaning).
    *   `chunk_size`: How big each piece should be (e.g., 500 characters).
    *   `chunk_overlap`: How much previous text to repeat in the next chunk (to prevent cutting sentences in half).

### 💡 Why use it?
*   **Fix "Broken" Answers:** If the AI answers the first part of your question but ignores the second part, paste your text here. You might see that your paragraph was split into two separate chunks, and the AI only found one of them.
*   **Visualize "Overlap":** See with your own eyes how `chunk_overlap` repeats the end of one chunk at the start of the next, ensuring no context is lost at the boundary.

---

## 3. Retrieval Debugger (`/v1/testing/retrieval`)

### 🎯 Goal
To answer the question: **"Why did the bot say 'I don't know'?"**

Often, the LLM gives a bad answer not because it's "dumb," but because it wasn't given the right information. This endpoint lets you bypass the LLM and look directly into the "brain" of the database.

### ⚙️ How to use
You act like the search engine. You send a query (e.g., "project deadline") and a Knowledge Base ID. The API returns the exact text chunks the system *would* have sent to the LLM, along with a "Relevance Score."

### 📥 Parameters
*   `query` (string): The question you want to test.
*   `kb_id` (string): The ID of the Knowledge Base (you can get this from the URL in the frontend).
*   `retrieval_config` (object):
    *   `strategy`: Choose how to search ("dense" for meaning, "sparse" for keywords, "rrf" for both).
    *   `top_k`: How many chunks to fetch (default is 5).

### 💡 Why use it?
*   **Diagnose "Hallucinations":** If the bot makes things up, check this endpoint. If the retrieved chunks don't contain the answer, the bot *had* to hallucinate. The fix is better data, not a better prompt.
*   **Compare Strategies:** Try searching for a specific error code like "Error 503".
    *   *Dense Search* might fail (it looks for "server issues").
    *   *Sparse Search* will likely succeed (it looks for "503").
    *   This helps you decide which strategy is best for your data.

---

## 4. Embedding Lab (`/v1/testing/embedding-relevance`)

### 🎯 Goal
To scientifically prove: **"Does this AI model actually understand English?"**

Embeddings are just lists of numbers. It's hard to trust them. This tool lets you run a controlled experiment to see if the model can tell the difference between a good match and a bad match.

### ⚙️ How to use
You set up a simple test case:
1.  **Query:** "Apple"
2.  **Relevant Text:** "The iPhone is a popular smartphone." (Should match well)
3.  **Irrelevant Text:** "Bananas are yellow." (Should match poorly)

The API calculates a **Similarity Score** (from 0.0 to 1.0) for both.
*   **Success:** Relevant Score (e.g., 0.85) >> Irrelevant Score (e.g., 0.20).
*   **Failure:** Relevant Score (0.75) ≈ Irrelevant Score (0.74).

### 📥 Parameters
*   `query` (string): The concept you are testing.
*   `relevant_text` (string): A text that *should* be found.
*   `irrelevant_text` (string): A text that *should be ignored*.
*   `models` (list): Which models to test (e.g., ["dense", "multi_vector"]).

### 💡 Why use it?
*   **Verify Nuance:** Test a tricky query like "Bank" (river) vs "Bank" (money).
    *   *Relevant:* "We sat by the water."
    *   *Irrelevant:* "I deposited a check."
    *   A good model will score the "water" text higher if the query implies a river context.
*   **Build Trust:** Seeing the scores helps you trust that the math behind the system is actually working.
