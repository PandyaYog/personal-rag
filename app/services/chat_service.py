import uuid
from sqlalchemy.orm import Session
from qdrant_client import models

from app.db.models.user import User
from app.db.models.assistant import Assistant, Chat, Message
from app.schemas.chat import UserQuery
from app.schemas.knowledgebase import EmbeddingModelConfig
from app.services.query_classifier_service import classify_query
from app.rag.retrieval.search import get_retriever
from app.services.llm_service import llm_client

def handle_user_query(db: Session, query_in: UserQuery, chat_id: uuid.UUID, user: User) -> Message:
    """Main RAG orchestration logic."""
    # 1. Fetch chat and assistant
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise ValueError("Chat not found.")
    assistant: Assistant = chat.assistant

    # 2. Save user's message
    user_message = Message(chat_id=chat.id, role="user", text=query_in.query)
    db.add(user_message)
    db.commit()

    # 3. Classify the query
    classification = classify_query(db, query=query_in.query, assistant_id=assistant.id)
    print("ckpt0")
    response_text = ""
    reference_docs = []

    # 4. Execute logic based on classification
    if classification.query_type == "general":
        response_text = "Hello! I am an AI assistant designed to help you with your documents. How can I assist you today?"
    
    else: # 'specific_doc' or 'whole_kb'
        # 5. Build retriever with assistant-specific config
        print("dasvf", assistant.embedding_config)
        try:
            embedding_config_model = EmbeddingModelConfig(**assistant.embedding_config)
        except Exception as e:
            # This provides robust error handling if the config in the DB is ever malformed.
            raise ValueError(f"Invalid embedding configuration for assistant {assistant.id}: {e}")
        
        # Now, pass the Pydantic model instance to the retriever.
        retriever = get_retriever(embedding_config=embedding_config_model)
        
        print("CKPT1")
        # 6. Build search filters
        kb_ids = [str(kb.id) for kb in assistant.knowledge_bases]
        must_conditions = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user.id))),
            models.FieldCondition(key="kb_id", match=models.MatchAny(any=kb_ids))
        ]
        print("CKPT2")
        if classification.query_type == "specific_doc" and classification.doc_ids:
            must_conditions.append(
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=classification.doc_ids))
            )
        print("CKPT3")
        search_filter = models.Filter(must=must_conditions)
        print("CKPT4")
        # 7. Perform retrieval
        search_results = retriever.search(
            query=query_in.query,
            filters=search_filter,
            search_type=assistant.llm_config.get("search_type", "full_rrf")
        )
        print("CKPT5")
        # 8. Format context for LLM
        context = "\n\n---\n\n".join([hit.payload['chunk_content'] for hit in search_results])
        unique_doc_names = list(set([hit.payload['doc_name'] for hit in search_results]))
        reference_docs = unique_doc_names
        print("CKPT16")
        if not context:
            context = "No relevant information found in the knowledge base."
        print("CKPT7")
        # 9. Generate response with LLM
        response_text = llm_client.generate_response(
            model=assistant.llm_config['model'],
            system_prompt=assistant.llm_config['system_prompt'],
            user_query=query_in.query,
            context=context,
            temp=assistant.llm_config['temperature'],
            top_p=assistant.llm_config['top_p']
        )
        print("CKPT7")
    # 10. Save assistant's message
    assistant_message = Message(
        chat_id=chat.id,
        role="assistant",
        text=response_text,
        reference_docs=reference_docs
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message