# 🧠 Embedding Models & Qdrant Configuration

This project utilizes a sophisticated **Multi-Model Embedding Architecture**. Instead of relying on a single vector representation, we generate three distinct types of embeddings for every document chunk. This allows us to capture different aspects of the text: semantic meaning, exact keywords, and fine-grained token interactions.

This document explains the three embedding types, the specific models used, and how the Qdrant vector database is configured to store them efficiently.

---

## 1. The Three Embedding Types

### A. Dense Embeddings (Semantic)
*   **What is it?** A single fixed-length vector (e.g., 768 numbers) representing the "average" meaning of the text.
*   **Role:** The workhorse of RAG. It finds documents that are *conceptually* similar to the query.
*   **Current Model:** `sentence-transformers/all-MiniLM-L6-v2` (or similar).
*   **Dimension:** `768` (Configurable).
*   **Library:** `fastembed` (Optimized ONNX runtime).

### B. Sparse Embeddings (Keyword / SPLADE)
*   **What is it?** A vector where most values are zero, except for specific indices corresponding to important words in the text.
*   **Role:** Acts like a "super-charged" keyword search. It learns which words are actually important (e.g., "Python" is important, "the" is not) and assigns weights to them.
*   **Current Model:** `prithivida/Splade_PP_en_v1`.
*   **Structure:** Stored as a list of `indices` (word IDs) and `values` (weights).

### C. Multi-Vector Embeddings (Late Interaction / ColBERT)
*   **What is it?** Instead of squashing a sentence into one vector, it creates a vector for *every single token* (word part).
*   **Role:** High-precision matching. It allows the system to compare "Apple" in the query specifically with "Apple" in the document, even if the surrounding context is different.
*   **Current Model:** `colbert-ir/colbertv2.0`.
*   **Dimension:** `128` per token.
*   **Comparator:** Uses `MaxSim` (Maximum Similarity) to find the best match for each query token.

---

## 2. Qdrant Collection Configuration

We use **Qdrant** as our vector engine because it natively supports all three embedding types in a single collection. Here is a breakdown of the configuration parameters used in `qdrant_service.py`:

### 📦 Vector Configuration (`vectors_config`)

#### Dense Vector Config
```python
"dense": models.VectorParams(
    size=768, 
    distance=models.Distance.COSINE
)
```
*   **`size=768`**: Must match the output dimension of your Dense model.
*   **`distance=COSINE`**: The industry standard for semantic similarity.
    *   **Why?** It measures the *angle* between two vectors, ignoring their length (magnitude). This is perfect for text embeddings where the "direction" represents the meaning.
    *   **Result:** A score of 1.0 means identical meaning, 0.0 means unrelated.

#### Multi-Vector Config
```python
"multi_vector": models.VectorParams(
    size=128,
    distance=models.Distance.DOT,
    multivector_config=models.MultiVectorConfig(
        comparator=models.MultiVectorComparator.MAX_SIM
    )
)
```
*   **`size=128`**: ColBERT vectors are smaller (128) but there are many of them.
*   **`distance=DOT`**: The Dot Product.
    *   **Why?** For *normalized* vectors (length = 1), Dot Product is mathematically identical to Cosine Similarity but is computationally faster to calculate (fewer operations).
    *   **Optimization:** Since ColBERT generates many vectors per document, this small speedup adds up to significant performance gains during retrieval.
*   **`comparator=MAX_SIM`**: This is the magic. It tells Qdrant to compare *every query vector* to *every document vector* and take the maximum similarity. This is what makes "Late Interaction" work.

### 🗂️ Sparse Vector Config (`sparse_vectors_config`)
```python
"sparse": models.SparseVectorParams(
    index=models.SparseIndexParams(
        on_disk=False, 
    )
)
```
*   **`on_disk=False`**: We keep the sparse index in RAM for maximum speed. If your dataset grows to millions of documents, you might flip this to `True` to save RAM at the cost of slight latency.

### ⚡ Performance & Optimization

#### HNSW Index (`hnsw_config`)
HNSW (Hierarchical Navigable Small World) is the algorithm Qdrant uses to find the closest vectors without scanning the entire database. It builds a graph where vectors are nodes and similar vectors are connected by edges.

```python
hnsw_config=models.HnswConfigDiff(
    m=16, 
    ef_construct=100, 
)
```
*   **`m=16` (Edges per Node):**
    *   **What it does:** Controls how many connections each node has in the graph.
    *   **Impact on RAG:**
        *   **Higher (e.g., 32, 64):** Better search accuracy (Recall) for complex datasets, but uses **more RAM** and makes indexing slower.
        *   **Lower (e.g., 8, 16):** Uses less RAM and indexes faster, but might miss some relevant documents in very large datasets (1M+ chunks).
    *   **Verdict:** `16` is a solid balance for datasets up to a few million vectors.

*   **`ef_construct=100` (Search Depth during Build):**
    *   **What it does:** Controls how "thorough" the system is when adding a new vector to the index. It checks 100 neighbors to find the absolute best spot for the new node.
    *   **Impact on RAG:**
        *   **Higher (e.g., 200, 400):** Significantly increases **Indexing Time** (document ingestion is slower), but results in a higher quality graph, leading to faster and more accurate searches later.
        *   **Lower (e.g., 40):** Fast ingestion, but the graph might be "messy," leading to slightly worse search results.
    *   **Verdict:** We prioritize search quality over ingestion speed, so `100` is a good default.

**⚠️ Pipeline Trade-off:**
If you notice your RAG system missing relevant documents (Low Recall), try increasing `ef_construct` to 200. If you run out of RAM, decrease `m` to 8.

#### Quantization (`quantization_config`)
```python
quantization_config=models.ScalarQuantization(
    scalar=models.ScalarQuantizationConfig(
        type=models.ScalarType.INT8,
        quantile=0.99,
        always_ram=True,
    ),
)
```
*   **`type=INT8`**: We compress the 32-bit floating point numbers into 8-bit integers.
*   **Impact:** Reduces memory usage by **4x** with negligible loss in accuracy.
*   **`always_ram=True`**: Ensures these compressed vectors stay in fast memory.

---

## 🔮 Future Flexibility & Parameters

Currently, the system uses "safe default" parameters optimized for general-purpose use. However, every parameter listed above represents a trade-off:

*   **Dimensions:** We currently use `768` for dense vectors. We plan to support switching to `384` (faster, mobile-friendly) or `1536` (OpenAI-compatible) in the future.
*   **HNSW Parameters:** For massive datasets (1M+ chunks), we would tune `m` and `ef_construct` to balance RAM usage vs. recall.
*   **Quantization:** We could explore `BinaryQuantization` (1-bit) for extreme speed, though it requires larger vector dimensions to maintain accuracy.

This architecture is built to be modular. Changing a model simply requires updating the `config` and recreating the collection—the pipeline handles the rest.
