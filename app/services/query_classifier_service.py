from typing import List, Literal, NamedTuple, Dict
from sqlalchemy.orm import Session
from thefuzz import process

from app.services import llm_service, kb_service 

CLASSIFICATION_MODEL = "llama-3.3-70b-versatile" 

CLASSIFICATION_SYSTEM_PROMPT = """
You are an expert query classifier. Your task is to determine the user's intent based on their query.
Classify the query into one of three categories:
1.  `general`: For greetings, conversational filler, or questions about the chatbot itself (e.g., "hello", "who are you?", "what can you do?").
2.  `specific_doc`: When the user is asking about a specific document or file by name (e.g., "what is in the project_proposal.pdf?", "summarize the annual_report.docx").
3.  `whole_kb`: For any other question that requires retrieving information from the knowledge base but does not mention a specific document name.

You must respond with ONLY one word: `general`, `specific_doc`, or `whole_kb`.
"""

class ClassificationResult(NamedTuple):
    query_type: Literal["general", "specific_doc", "whole_kb"]
    doc_ids: List[str] | None = None

def classify_query(db: Session, query: str, assistant_id: str) -> ClassificationResult:
    """
    Uses an LLM call to classify the user's query and then identifies any mentioned documents.
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
            max_tokens=5, # We only need one word
        ).choices[0].message.content.lower().strip()

        # Clean the response to be safe
        if 'general' in raw_classification:
            query_type = "general"
        elif 'specific_doc' in raw_classification:
            query_type = "specific_doc"
        else:
            query_type = "whole_kb"
        
        print(f"LLM classified query as: '{query_type}'")

        # 2. If classified as specific_doc, find the document ID
        if query_type == "specific_doc":
            docs_in_kbs = kb_service.get_all_docs_for_assistant(db, assistant_id=assistant_id)
            if docs_in_kbs:
                doc_names_map: Dict[str, str] = {doc.name: str(doc.id) for doc in docs_in_kbs}
                best_match = process.extractOne(query, doc_names_map.keys())
                
                # A lower threshold is acceptable here since the LLM already confirmed the intent.
                if best_match and best_match[1] > 75: 
                    matched_doc_name = best_match[0]
                    matched_doc_id = doc_names_map[matched_doc_name]
                    print(f"Found specific document mention: '{matched_doc_name}' (ID: {matched_doc_id})")
                    return ClassificationResult(query_type="specific_doc", doc_ids=[matched_doc_id])
                else:
                    # If fuzzy matching fails, revert to whole_kb search.
                    print("LLM classified as 'specific_doc' but no document name matched. Reverting to 'whole_kb'.")
                    return ClassificationResult(query_type="whole_kb")
        
        # 3. Return the classification result for general or whole_kb
        return ClassificationResult(query_type=query_type)

    except Exception as e:
        print(f"Error during LLM classification: {e}. Defaulting to 'whole_kb' search.")
        return ClassificationResult(query_type="whole_kb")