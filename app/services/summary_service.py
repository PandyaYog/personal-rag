"""
Summary Service
===============
Provides document summary generation using an adaptive Map-Reduce strategy
and handles storage of summaries into the dedicated Qdrant summary collection.

Designed to run inside a Celery worker — all operations are synchronous
and avoid holding large objects in memory longer than necessary.
"""

import uuid
import logging
from typing import Tuple

from qdrant_client import models as qdrant_models

from app.services.llm_service import llm_client
from app.services.qdrant_service import qdrant_service
from app.rag.embedding.models import get_embedder
from app.schemas.knowledgebase import EmbeddingModelConfig

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

# Rough heuristic: 1 token ≈ 4 characters. 
# Conservative to stay within Groq context windows.
CHARS_PER_TOKEN = 4
STUFFING_TOKEN_LIMIT = 6000         # Below this → single-shot summary
MAP_CHUNK_TOKEN_LIMIT = 4000        # Each "map" window size
MAP_CHUNK_CHAR_LIMIT = MAP_CHUNK_TOKEN_LIMIT * CHARS_PER_TOKEN
STUFFING_CHAR_LIMIT = STUFFING_TOKEN_LIMIT * CHARS_PER_TOKEN

SUMMARY_MODEL = "llama-3.3-70b-versatile"
SUMMARY_TEMPERATURE = 0.3
SUMMARY_TOP_P = 1.0

# ─── Prompts ──────────────────────────────────────────────────────────────────

STUFFING_PROMPT = """You are a precise document summarizer.
Create a comprehensive summary of the following document.
Capture ALL key topics, facts, figures, names, dates, and conclusions.
Structure the summary with clear sections if the document covers multiple topics.
Do NOT add any information that is not present in the text.
Do NOT start with phrases like "Here is a summary" — just provide the summary directly."""

MAP_SECTION_PROMPT = """You are a precise document summarizer.
Summarize the following section of a larger document.
Capture ALL key points, facts, figures, and important details from this section.
Be thorough — this section summary will be combined with others to form the full document summary.
Do NOT add any information that is not present in the text.
Do NOT start with phrases like "Here is a summary" — just provide the summary directly."""

REDUCE_PROMPT = """You are a precise document summarizer.
Below are summaries of individual sections of a document titled '{doc_name}'.
Combine them into a single, coherent, and comprehensive summary.
Remove redundancy but preserve ALL unique information, facts, and conclusions.
Structure the final summary logically with clear flow between topics.
Do NOT add any information not present in the section summaries."""


# ─── Core Summary Generation ─────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """Estimates token count using character-based heuristic."""
    return len(text) // CHARS_PER_TOKEN


def _split_into_map_chunks(text: str) -> list[str]:
    """
    Splits text into chunks of approximately MAP_CHUNK_CHAR_LIMIT characters,
    breaking at paragraph boundaries when possible to preserve context.
    """
    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= MAP_CHUNK_CHAR_LIMIT:
            chunks.append(remaining)
            break

        # Try to find a paragraph break near the limit
        split_point = remaining.rfind("\n\n", 0, MAP_CHUNK_CHAR_LIMIT)
        if split_point == -1 or split_point < MAP_CHUNK_CHAR_LIMIT // 2:
            # Fallback: split at the last newline within the limit
            split_point = remaining.rfind("\n", 0, MAP_CHUNK_CHAR_LIMIT)
        if split_point == -1 or split_point < MAP_CHUNK_CHAR_LIMIT // 2:
            # Hard split at the character limit
            split_point = MAP_CHUNK_CHAR_LIMIT

        chunks.append(remaining[:split_point].strip())
        remaining = remaining[split_point:].strip()

    return [c for c in chunks if c]  # Filter out empty chunks


def _llm_summarize(text: str, system_prompt: str) -> str:
    """
    Makes a single LLM call for summarization.
    Wraps the GroqClient with error handling suitable for Celery tasks.
    """
    try:
        response = llm_client.generate_response(
            model=SUMMARY_MODEL,
            system_prompt=system_prompt,
            user_query=text,
            context="",
            temp=SUMMARY_TEMPERATURE,
            top_p=SUMMARY_TOP_P
        )
        return response.strip()
    except Exception as e:
        logger.error(f"LLM summarization call failed: {e}")
        raise


def generate_document_summary(full_text: str, doc_name: str) -> Tuple[str, str]:
    """
    Generates a comprehensive summary of a document using an adaptive strategy.
    
    - Small docs (< STUFFING_TOKEN_LIMIT tokens): Single-shot "stuffing" approach.
    - Large docs: Map-Reduce — summarize each section, then consolidate.
    
    Args:
        full_text: The complete extracted text of the document.
        doc_name: The filename, used in the consolidation prompt for context.
        
    Returns:
        A tuple of (summary_text, method_used) where method_used is 
        either "stuffing" or "map_reduce".
        
    Raises:
        ValueError: If the input text is empty or whitespace-only.
        Exception: If LLM calls fail after the text has been validated.
    """
    if not full_text or not full_text.strip():
        raise ValueError(f"Cannot generate summary for '{doc_name}': document text is empty.")

    estimated_tokens = _estimate_tokens(full_text)
    logger.info(
        f"Generating summary for '{doc_name}' "
        f"(~{estimated_tokens} tokens, ~{len(full_text)} chars)"
    )

    if estimated_tokens < STUFFING_TOKEN_LIMIT:
        # ── Stuffing Strategy ─────────────────────────────────────────────
        logger.info(f"Using STUFFING strategy for '{doc_name}'")
        summary = _llm_summarize(full_text, STUFFING_PROMPT)
        return summary, "stuffing"
    else:
        # ── Map-Reduce Strategy ───────────────────────────────────────────
        map_chunks = _split_into_map_chunks(full_text)
        logger.info(
            f"Using MAP-REDUCE strategy for '{doc_name}' "
            f"({len(map_chunks)} map chunks)"
        )

        # MAP phase: Summarize each chunk independently
        section_summaries = []
        for i, chunk in enumerate(map_chunks):
            logger.info(f"  Map step {i + 1}/{len(map_chunks)} for '{doc_name}'")
            section_summary = _llm_summarize(chunk, MAP_SECTION_PROMPT)
            section_summaries.append(section_summary)

        # REDUCE phase: Consolidate all section summaries
        combined_sections = "\n\n---\n\n".join(
            [f"Section {i + 1}:\n{s}" for i, s in enumerate(section_summaries)]
        )
        reduce_prompt = REDUCE_PROMPT.format(doc_name=doc_name)
        
        # Check if combined sections themselves exceed the limit
        # (extremely large documents with many sections)
        if _estimate_tokens(combined_sections) > STUFFING_TOKEN_LIMIT:
            logger.info(f"  Combined sections too large, performing recursive reduce for '{doc_name}'")
            # Recursive reduce: split combined sections and reduce again
            reduce_chunks = _split_into_map_chunks(combined_sections)
            intermediate_summaries = []
            for j, rc in enumerate(reduce_chunks):
                logger.info(f"  Recursive reduce {j + 1}/{len(reduce_chunks)}")
                intermediate = _llm_summarize(rc, reduce_prompt)
                intermediate_summaries.append(intermediate)
            
            final_input = "\n\n---\n\n".join(intermediate_summaries)
            summary = _llm_summarize(final_input, reduce_prompt)
        else:
            summary = _llm_summarize(combined_sections, reduce_prompt)

        return summary, "map_reduce"


# ─── Qdrant Storage ──────────────────────────────────────────────────────────

def store_summary_in_qdrant(
    summary_text: str,
    summary_method: str,
    doc,       # Document ORM instance
    kb,        # KnowledgeBase ORM instance
    embedding_config: EmbeddingModelConfig,
    chunk_count: int
) -> None:
    """
    Embeds the summary text and stores it in the dedicated Qdrant summary collection.
    
    Uses only the dense vector from the embedder since the summary collection
    is configured for dense-only storage.
    
    Args:
        summary_text: The generated summary string.
        summary_method: Either "stuffing" or "map_reduce".
        doc: The Document ORM instance (provides id, name, user_id).
        kb: The KnowledgeBase ORM instance (provides id).
        embedding_config: The KB's embedding configuration for the dense model.
        chunk_count: Number of chunks the document was split into.
        
    Raises:
        Exception: If embedding or Qdrant upsert fails.
    """
    try:
        # Embed the summary using the KB's configured dense embedder
        embedder = get_embedder(config=embedding_config)
        embeddings = embedder.embed([summary_text])[0]

        dense_vector = embeddings.get("dense")
        if dense_vector is None:
            raise ValueError("Embedding service did not return a dense vector for the summary.")

        # Build the payload
        payload = {
            "kb_id": str(kb.id),
            "doc_id": str(doc.id),
            "doc_name": doc.name,
            "user_id": str(doc.user_id),
            "summary_text": summary_text,
            "summary_method": summary_method,
            "chunk_count": chunk_count,
        }

        # Build the point with a deterministic-ish UUID
        point = qdrant_models.PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": dense_vector},
            payload=payload
        )

        qdrant_service.upsert_summary_point(point)
        logger.info(f"Summary stored in Qdrant for doc '{doc.name}' (method: {summary_method})")

    except Exception as e:
        logger.error(f"Failed to store summary in Qdrant for doc '{doc.name}': {e}")
        raise


# ─── Orchestrator (called from Celery task) ───────────────────────────────────

def generate_and_store_summary(
    full_text: str,
    doc,
    kb,
    embedding_config: EmbeddingModelConfig
) -> None:
    """
    Top-level orchestrator that generates a document summary and stores it in Qdrant.
    Designed to be called directly from the Celery document processing pipeline.
    
    This function is intentionally synchronous and self-contained so it can 
    run safely inside a Celery worker process.
    
    Args:
        full_text: The complete extracted text of the document.
        doc: The Document ORM instance.
        kb: The KnowledgeBase ORM instance.
        embedding_config: The KB's embedding config (EmbeddingModelConfig).
        
    Note:
        Failures in summary generation do NOT cause the entire document
        processing task to fail. The document will still be marked COMPLETED
        but without a summary. The error is logged for debugging.
    """
    try:
        # Delete any existing summary for this doc (handles reprocessing)
        qdrant_service.delete_summary_by_doc_id(str(doc.id))

        # Generate the summary
        summary_text, method = generate_document_summary(full_text, doc.name)
        logger.info(
            f"Summary generated for '{doc.name}' using {method} "
            f"({len(summary_text)} chars)"
        )

        # Store in Qdrant
        store_summary_in_qdrant(
            summary_text=summary_text,
            summary_method=method,
            doc=doc,
            kb=kb,
            embedding_config=embedding_config,
            chunk_count=doc.num_chunks or 0
        )

    except ValueError as e:
        # Empty text or validation errors — log but don't crash the pipeline
        logger.warning(f"Skipping summary for '{doc.name}': {e}")
    except Exception as e:
        # LLM or Qdrant failures — log but don't crash the pipeline
        logger.error(
            f"Summary generation/storage failed for '{doc.name}': {e}. "
            f"Document processing will continue without a summary."
        )
