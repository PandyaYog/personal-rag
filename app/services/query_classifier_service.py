import logging
from typing import List, Literal, NamedTuple, Dict
from sqlalchemy.orm import Session
from thefuzz import process

from app.services import llm_service, kb_service 

logger = logging.getLogger(__name__)

CLASSIFICATION_MODEL = "llama-3.3-70b-versatile" 

CLASSIFICATION_SYSTEM_PROMPT = """You are an expert query classifier for a Retrieval-Augmented Generation (RAG) system.
Your task is to determine the user's intent and classify it into exactly ONE of FIVE categories.

## Categories

1. `general`
   Use this when the user is making casual conversation, greeting, asking about the chatbot's capabilities, 
   or asking something completely unrelated to any document or knowledge base content.

2. `specific_doc`
   Use this when the user is asking a QUESTION about the CONTENT inside a specific document or file. 
   The user mentions or references a document by name and wants to extract specific information from it.
   This is NOT for summaries — it is for targeted factual questions about a document's content.

3. `whole_kb`
   Use this when the user asks a knowledge-related question that requires searching across ALL documents 
   in the knowledge base. The user does NOT mention a specific document name. They want an answer 
   that may come from any source in the knowledge base.

4. `count`
   Use this when the user is asking about metadata, statistics, or inventory of the knowledge base itself.
   Examples include asking how many documents exist, what files have been uploaded, or what the data sources are.
   The user is NOT asking about the content of the documents — they are asking ABOUT the documents.

5. `summary`
   Use this when the user explicitly asks for a summary, overview, brief, or high-level description of 
   a specific document or of all documents. Keywords like "summarize", "overview", "what is it about", 
   "brief me on", "give me the gist" strongly indicate this category.

## Examples

### general
- "Hello, how are you?"
- "What can you do?"
- "Who built you?"
- "Tell me a joke"
- "Thank you for your help"

### specific_doc
- "What are the key findings in the Q3_financial_report.pdf?"
- "What date is mentioned in the contract_agreement.docx?"
- "List all the action items from meeting_notes.pdf"
- "What is the salary range mentioned in the offer_letter.pdf?"
- "Who is the author of the research_paper.pdf?"

### whole_kb
- "What are our company's core values?"
- "How do I request time off?"
- "What is the refund policy?"
- "Explain the onboarding process for new employees"
- "What security protocols should I follow?"

### count
- "How many documents are in the knowledge base?"
- "What files have been uploaded?"
- "What are the sources of your data?"
- "List all documents available"
- "How many files do you have access to?"

### summary
- "Summarize the project_plan.pdf"
- "Give me an overview of the annual_report.docx"
- "What is the employee_handbook.pdf about?"
- "Brief me on all the documents"
- "Give me the gist of the research_paper.pdf"

## Rules
- Respond with ONLY one word: `general`, `specific_doc`, `whole_kb`, `count`, or `summary`.
- If unsure between `specific_doc` and `summary`, choose `summary` if the user wants a broad overview, choose `specific_doc` if the user wants a specific fact or detail.
- If unsure between `whole_kb` and `summary`, choose `summary` if the user uses words like "summarize", "overview", "about", "gist", "brief".
"""


class ClassificationResult(NamedTuple):
    query_type: Literal["general", "specific_doc", "whole_kb", "count", "summary"]
    doc_ids: List[str] | None = None


def _fuzzy_match_document(query: str, db: Session, assistant_id: str) -> List[str] | None:
    """
    Attempts to identify a specific document mentioned in the query using fuzzy matching 
    against all documents available to the assistant.
    
    Args:
        query: The user's raw query string.
        db: Database session.
        assistant_id: The assistant's UUID string.
        
    Returns:
        A list containing the matched document ID, or None if no match is found.
    """
    docs_in_kbs = kb_service.get_all_docs_for_assistant(db, assistant_id=assistant_id)
    if not docs_in_kbs:
        return None
        
    doc_names_map: Dict[str, str] = {doc.name: str(doc.id) for doc in docs_in_kbs}
    best_match = process.extractOne(query, doc_names_map.keys())
    
    # A lower threshold is acceptable since the LLM already confirmed the intent.
    if best_match and best_match[1] > 70:
        matched_doc_name = best_match[0]
        matched_doc_id = doc_names_map[matched_doc_name]
        logger.info(f"Fuzzy matched document: '{matched_doc_name}' (ID: {matched_doc_id}, score: {best_match[1]})")
        return [matched_doc_id]
    
    return None


def classify_query(db: Session, query: str, assistant_id: str) -> ClassificationResult:
    """
    Uses an LLM call to classify the user's query into one of five categories,
    then performs fuzzy document matching for doc-specific intents.
    
    Classification Categories:
        - general: Casual conversation, greetings, chatbot meta-questions.
        - specific_doc: Targeted question about a named document's content.
        - whole_kb: Knowledge question requiring cross-document search.
        - count: Questions about KB metadata/statistics.
        - summary: Requests for document summaries or overviews.
        
    Args:
        db: Database session for document lookups.
        query: The user's raw query string.
        assistant_id: The assistant's UUID string.
        
    Returns:
        ClassificationResult with the query_type and optional doc_ids.
    """
    try:
        # 1. Use LLM to get the high-level classification
        raw_classification = llm_service.llm_client.client.chat.completions.create(
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            model=CLASSIFICATION_MODEL,
            temperature=0.0,
            max_tokens=5,
        ).choices[0].message.content.lower().strip()

        # 2. Parse the LLM response safely
        if 'summary' in raw_classification:
            query_type = "summary"
        elif 'general' in raw_classification:
            query_type = "general"
        elif 'specific_doc' in raw_classification:
            query_type = "specific_doc"
        elif 'count' in raw_classification:
            query_type = "count"
        else:
            query_type = "whole_kb"
        
        logger.info(f"LLM classified query as: '{query_type}' (raw: '{raw_classification}')")

        # 3. For doc-specific intents, attempt to identify the document
        if query_type in ("specific_doc", "summary"):
            matched_ids = _fuzzy_match_document(query, db, assistant_id)
            
            if matched_ids:
                return ClassificationResult(query_type=query_type, doc_ids=matched_ids)
            else:
                if query_type == "specific_doc":
                    # No doc matched → fall back to whole_kb search
                    logger.info("No document matched for 'specific_doc'. Falling back to 'whole_kb'.")
                    return ClassificationResult(query_type="whole_kb")
                else:
                    # summary without a specific doc → user wants a general overview of all docs
                    logger.info("No document matched for 'summary'. Will summarize all available docs.")
                    return ClassificationResult(query_type="summary", doc_ids=None)
        
        # 4. Return the classification for general, whole_kb, or count
        return ClassificationResult(query_type=query_type)

    except Exception as e:
        logger.error(f"Error during LLM classification: {e}. Defaulting to 'whole_kb' search.")
        return ClassificationResult(query_type="whole_kb")