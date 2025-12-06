import uuid
from ..core.celery_app import celery_app
from sqlalchemy.orm import Session
from qdrant_client import models
from ..schemas.knowledgebase import EmbeddingModelConfig
from app.db.session import SessionLocal
from app.services import document_service, kb_service, minio_service, qdrant_service
from app.rag.chunking.methods import get_chunker
from app.rag.embedding.models import get_embedder
from app.rag.parsing import extract_text_from_file

@celery_app.task
def process_document_task(doc_id_str: str):
    db: Session = SessionLocal()
    doc = None
    try:
        doc_id = uuid.UUID(doc_id_str)
        doc = document_service.get_doc_by_id_internal(db, doc_id=doc_id) 
        if not doc:
            print(f"Task failed: Document with id {doc_id} not found.")
            return

        kb = doc.kb
        doc.processing_status = "PROCESSING"
        db.commit()
        print(f"Processing doc: {doc.name} ({doc.id}) for KB: {kb.name}")

        qdrant_service.qdrant_service.delete_points_by_doc_id(doc_id=str(doc.id))

        # 1. Download from Minio and Parse
        file_data = minio_service.minio_client.get_object_file(doc.file_path_in_minio)
        full_text = extract_text_from_file(file_data, doc.name)

        # 2. Chunk the text
        chunker = get_chunker(kb.chunking_strategy)
        chunks = chunker.chunk(full_text)

        # 3. Embed the chunks
        print(f"Embedding with config: {kb.embedding_model}")
        if isinstance(kb.embedding_model, dict):
            embedding_config = EmbeddingModelConfig(**kb.embedding_model)
        else:
            embedding_config = kb.embedding_model
        
        embedder = get_embedder(config=embedding_config)

        # 4. Embed and Upsert in Batches
        batch_size = 32  
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embedder.embed(batch_chunks)
            
            points_to_upsert = []
            for j, (chunk_text, embedding_dict) in enumerate(zip(batch_chunks, batch_embeddings)):
                point_id = str(uuid.uuid4())
                payload = {
                    "kb_id": str(kb.id),
                    "doc_id": str(doc.id),
                    "doc_name": doc.name,
                    "user_id": str(doc.user_id),
                    "chunk_num": i + j + 1,
                    "chunk_content": chunk_text,
                }
                
                vector_payload = {}
                if embedding_dict.get('dense') is not None:
                    vector_payload['dense'] = embedding_dict['dense']
                if embedding_dict.get('sparse') is not None:
                    vector_payload['sparse'] = embedding_dict['sparse']
                if embedding_dict.get('multi_vector') is not None:
                    vector_payload['multi_vector'] = embedding_dict['multi_vector']
                
                if vector_payload: 
                    points_to_upsert.append(
                        models.PointStruct(id=point_id, vector=vector_payload, payload=payload)
                    )
            
            if points_to_upsert:
                qdrant_service.qdrant_service.upsert_points(points=points_to_upsert)

        # 7. Update status to COMPLETED
        doc.processing_status = "COMPLETED"
        doc.num_chunks = len(chunks)
        print(f"Successfully processed document: {doc.name}")

    except Exception as e:
        print(f"Error processing document {doc_id_str}: {e}")
        if doc:
            doc.processing_status = "FAILED"
        raise
    finally:
        if doc:
            db.commit()
        db.close()