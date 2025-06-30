import uuid
from sqlalchemy.orm import Session
from qdrant_client import models
from sqlalchemy import desc
from typing import List
from app.db.models.user import User
from app.db.models.assistant import Assistant, Chat, Message
from app.schemas.chat import UserQuery, ChatUpdate
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
    query = original_user_message.content['text']
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

def perform_rag_pipeline(db, query, assistant, user):
    classification = classify_query(db, query=query, assistant_id=assistant.id)
    
    if classification.query_type == "general":
        return "Hello! I am an AI assistant. How can I help?", []

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