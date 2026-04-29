import uuid
import logging
from sqlalchemy.orm import Session
from qdrant_client import models
from sqlalchemy import desc
from typing import List, Tuple
from app.db.models.user import User
from app.db.models.assistant import Assistant, Chat, Message
from app.schemas.chat import UserQuery, ChatUpdate
from app.schemas.knowledgebase import EmbeddingModelConfig
from app.services.query_classifier_service import classify_query
from app.services.qdrant_service import qdrant_service as qdrant_svc
from app.rag.retrieval.search import get_retriever
from app.services.llm_service import llm_client

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = (
    "You are an AI assistant with access to pre-generated document summaries. "
    "Use the provided summary context to answer the user's query accurately. "
    "If the user asked for a summary, present the information in a clear and structured manner. "
    "Do not fabricate information beyond what is in the summaries."
)

def handle_user_query(db: Session, query_in: UserQuery, chat_id: uuid.UUID, user: User) -> Message:
    """Main RAG orchestration logic."""
    # 1. Fetch chat and assistant
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise ValueError("Chat not found.")
    assistant: Assistant = chat.assistant

    # 2. Save user's message
    user_message_content = {
        "versions": [
            {
                "version": 1,
                "text": query_in.query,
                "reference_docs": None 
            }
        ]
    }
    user_message = Message(
        chat_id=chat.id, 
        role="user", 
        content=user_message_content
    )
    db.add(user_message)
    db.commit()

    # 3. Classify the query
    classification = classify_query(db, query=query_in.query, assistant_id=assistant.id)
    logger.info(f"Query classified as: {classification.query_type}")
    response_text = ""
    reference_docs = []

    # 4. Execute logic based on classification
    if classification.query_type == "general":
        general_prompt = "You are a helpful AI assistant connected to a user's personal knowledge base. Respond to the following general query naturally and politely."
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=general_prompt,
            user_query=query_in.query,
            context="No context needed.",
            temp=0.7,
            top_p=1.0
        )
        
    elif classification.query_type == "count":
        from app.services import kb_service
        docs = kb_service.get_all_docs_for_assistant(db, assistant_id=assistant.id)
        doc_count = len(docs) if docs else 0
        doc_names = [doc.name for doc in docs] if docs else []
        context = f"The knowledge base currently contains {doc_count} documents. Sources: {', '.join(doc_names)}."
        
        count_prompt = "You are an AI assistant. Use the provided context to answer the user's question about the knowledge base statistics or data sources."
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=count_prompt,
            user_query=query_in.query,
            context=context,
            temp=0.3,
            top_p=1.0
        )
    elif classification.query_type == "summary":
        context, reference_docs = _build_summary_context(
            db, classification, assistant
        )
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_query=query_in.query,
            context=context,
            temp=0.3,
            top_p=1.0
        )
    
    else: # 'specific_doc' or 'whole_kb'
        # 5. Build retriever with assistant-specific config
        try:
            embedding_config_model = EmbeddingModelConfig(**assistant.embedding_config)
        except Exception as e:
            raise ValueError(f"Invalid embedding configuration for assistant {assistant.id}: {e}")
        
        retriever = get_retriever(embedding_config=embedding_config_model)
        
        # 6. Build search filters
        kb_ids = [str(kb.id) for kb in assistant.knowledge_bases]
        must_conditions = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user.id))),
            models.FieldCondition(key="kb_id", match=models.MatchAny(any=kb_ids))
        ]
        if classification.query_type == "specific_doc" and classification.doc_ids:
            must_conditions.append(
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=classification.doc_ids))
            )
        search_filter = models.Filter(must=must_conditions)
        
        # 7. Perform retrieval
        search_results = retriever.search(
            query=query_in.query,
            filters=search_filter,
            search_type=assistant.llm_config.get("search_type", "full_rrf")
        )
        
        # 8. Format context for LLM
        context = "\n\n---\n\n".join([hit.payload['chunk_content'] for hit in search_results])
        unique_doc_names = list(set([hit.payload['doc_name'] for hit in search_results]))
        reference_docs = unique_doc_names
        if not context:
            context = "No relevant information found in the knowledge base."
        
        # 9. Generate response with LLM
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=assistant.llm_config['system_prompt'],
            user_query=query_in.query,
            context=context,
            temp=assistant.llm_config['temperature'],
            top_p=assistant.llm_config['top_p']
        )
    # 10. Save assistant's message

    assistant_message_content = {
        "versions": [
            {
                "version": 1,
                "text": response_text,
                "reference_docs": reference_docs
            }
        ]
    }

    assistant_message = Message(
        chat_id=chat.id,
        role="assistant",
        content=assistant_message_content,
        parent_id=user_message.id
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message

def provide_feedback(db: Session, chat_id: uuid.UUID, message_id: uuid.UUID, is_good: bool, user: User) -> Message:
    """
    Updates the feedback status (is_good) for a specific assistant message.
    """
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id,
        Message.role == 'assistant'
    ).first()

    if not message:
        raise ValueError("Message not found.")
        
    if message.chat.user_id != user.id:
        raise ValueError("User does not have permission to provide feedback on this message.")

    message.is_good = is_good
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_all_chats_for_assistant(db: Session, assistant_id: uuid.UUID, user_id: uuid.UUID) -> List[Chat]:
    """
    Retrieves all chats associated with a specific assistant for a given user.
    """
    chats = db.query(Chat).filter(
        Chat.assistant_id == assistant_id,
        Chat.user_id == user_id
    ).order_by(desc(Chat.updated_at)).all() 
    
    return chats

def update_chat_name(db: Session, chat_id: uuid.UUID, chat_in: ChatUpdate, user_id: uuid.UUID) -> Chat:
    """
    Updates the name of a specific chat.
    """
    db_chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not db_chat:
        raise ValueError("Chat not found.")
    
    db_chat.name = chat_in.name
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return db_chat

def delete_chat(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID):
    """
    Deletes a chat and all its associated messages.
    """
    db_chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    
    if not db_chat:
        raise ValueError("Chat not found.")
        
    db.delete(db_chat)
    db.commit()

def regenerate_response(db: Session, chat_id: uuid.UUID, message_id: uuid.UUID, user: User) -> Message:
    """
    Finds a user query via parent_id, generates a new response, 
    and appends it as a new version to the assistant's message.
    """
    # 1. Fetch the target assistant message to regenerate
    assistant_message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id,
        Message.role == 'assistant'
    ).first()

    if not assistant_message:
        raise ValueError("Assistant message to regenerate not found.")
    if assistant_message.chat.user_id != user.id:
        raise ValueError("User does not have permission.")
    if not assistant_message.parent_id:
        raise ValueError("Cannot regenerate a message that has no parent query.")

    # 2. Find the original user query using the parent_id
    original_user_message = db.query(Message).filter(Message.id == assistant_message.parent_id).first()
    if not original_user_message:
        raise ValueError("Original user query could not be found.")

    # 3. Re-run the RAG pipeline (Steps 3-8 from handle_user_query)
    query = original_user_message.content['versions'][-1]['text']
    assistant = assistant_message.chat.assistant
    
    new_response_text, new_reference_docs = perform_rag_pipeline(db, query, assistant, user)

    # 4. Append the new version to the existing message's content
    current_content = assistant_message.content
    new_version_number = len(current_content.get("versions", [])) + 1
    
    new_version = {
        "version": new_version_number,
        "text": new_response_text,
        "reference_docs": new_reference_docs
    }
    current_content["versions"].append(new_version)
    
    # 5. Update the message in the database
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(assistant_message, "content")
    
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message

def perform_rag_pipeline(db, query, assistant, user) -> Tuple[str, List[str]]:
    """
    Shared RAG pipeline used by both handle_user_query and regenerate_response.
    Routes queries through the appropriate handler based on classification.
    
    Returns:
        A tuple of (response_text, reference_docs).
    """
    classification = classify_query(db, query=query, assistant_id=assistant.id)
    
    if classification.query_type == "general":
        general_prompt = "You are a helpful AI assistant connected to a user's personal knowledge base. Respond to the following general query naturally and politely."
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=general_prompt,
            user_query=query,
            context="No context needed.",
            temp=0.7,
            top_p=1.0
        )
        return response_text, []
        
    elif classification.query_type == "count":
        from app.services import kb_service
        docs = kb_service.get_all_docs_for_assistant(db, assistant_id=assistant.id)
        doc_count = len(docs) if docs else 0
        doc_names = [doc.name for doc in docs] if docs else []
        context = f"The knowledge base currently contains {doc_count} documents. Sources: {', '.join(doc_names)}."
        
        count_prompt = "You are an AI assistant. Use the provided context to answer the user's question about the knowledge base statistics or data sources."
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=count_prompt,
            user_query=query,
            context=context,
            temp=0.3,
            top_p=1.0
        )
        return response_text, []

    elif classification.query_type == "summary":
        context, reference_docs = _build_summary_context(
            db, classification, assistant
        )
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_query=query,
            context=context,
            temp=0.3,
            top_p=1.0
        )
        return response_text, reference_docs

    # Default: specific_doc or whole_kb → vector search
    try:
        embedding_config_model = EmbeddingModelConfig(**assistant.embedding_config)
    except Exception as e:
        raise ValueError(f"Invalid embedding configuration for assistant {assistant.id}: {e}")
    
    retriever = get_retriever(embedding_config=embedding_config_model)
    kb_ids = [str(kb.id) for kb in assistant.knowledge_bases]
    must_conditions = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user.id))),
        models.FieldCondition(key="kb_id", match=models.MatchAny(any=kb_ids))
    ]
    if classification.query_type == "specific_doc" and classification.doc_ids:
        must_conditions.append(models.FieldCondition(key="doc_id", match=models.MatchAny(any=classification.doc_ids)))
    search_filter = models.Filter(must=must_conditions)
    search_results = retriever.search(query=query, filters=search_filter, search_type=assistant.llm_config.get("search_type", "full_rrf"))
    
    context = "\n\n---\n\n".join([hit.payload['chunk_content'] for hit in search_results])
    unique_doc_names = list(set([hit.payload['doc_name'] for hit in search_results]))
    
    if not context: context = "No relevant information found in the knowledge base."

    response_text = llm_client.generate_response(
        model=assistant.llm_config['model'],
        system_prompt=assistant.llm_config['system_prompt'],
        user_query=query, context=context,
        temp=assistant.llm_config['temperature'], top_p=assistant.llm_config['top_p']
    )
    return response_text, unique_doc_names


# ─── Summary Context Builder ─────────────────────────────────────────────────

def _build_summary_context(
    db: Session,
    classification,
    assistant: Assistant
) -> Tuple[str, List[str]]:
    """
    Builds the context string for summary-type queries by fetching pre-computed
    summaries from the Qdrant summary collection.
    
    Handles two cases:
        1. Specific document summary (doc_ids provided) — fetches one summary.
        2. General overview (no doc_ids) — fetches summaries for all docs in the assistant's KBs.
    
    Args:
        db: Database session.
        classification: The ClassificationResult from the query classifier.
        assistant: The Assistant ORM instance.
        
    Returns:
        A tuple of (context_string, reference_doc_names).
    """
    reference_docs = []

    if classification.doc_ids:
        # User asked for a specific document's summary
        doc_id = classification.doc_ids[0]
        summary_point = qdrant_svc.get_summary_by_doc_id(doc_id)
        
        if summary_point:
            context = summary_point.payload['summary_text']
            reference_docs = [summary_point.payload['doc_name']]
            logger.info(f"Retrieved summary for doc_id: {doc_id}")
        else:
            context = (
                "No pre-computed summary is available for this document yet. "
                "The document may still be processing. Please try again later."
            )
            logger.warning(f"No summary found in Qdrant for doc_id: {doc_id}")
    else:
        # User asked for a general overview of all documents
        all_summaries = []
        for kb in assistant.knowledge_bases:
            for doc in kb.documents:
                summary_point = qdrant_svc.get_summary_by_doc_id(str(doc.id))
                if summary_point:
                    doc_name = summary_point.payload['doc_name']
                    summary_text = summary_point.payload['summary_text']
                    all_summaries.append(f"## {doc_name}\n{summary_text}")
                    reference_docs.append(doc_name)
        
        if all_summaries:
            context = "\n\n---\n\n".join(all_summaries)
            logger.info(f"Retrieved summaries for {len(all_summaries)} documents")
        else:
            context = (
                "No document summaries are available yet. "
                "Documents may still be processing. Please try again later."
            )
            logger.warning("No summaries found for any documents in assistant's KBs")

    return context, reference_docs