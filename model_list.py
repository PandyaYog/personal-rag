
models_embedding = {
    "Dense": ['BAAI/bge-base-en', 
              'BAAI/bge-base-en-v1.5', 
              'snowflake/snowflake-arctic-embed-m', 
              'snowflake/snowflake-arctic-embed-m-long', 
              'jinaai/jina-clip-v1', 
              'jinaai/jina-embeddings-v2-base-en', 
              'jinaai/jina-embeddings-v2-base-de', 
              'jinaai/jina-embeddings-v2-base-code', 
              'jinaai/jina-embeddings-v2-base-zh', 
              'jinaai/jina-embeddings-v2-base-es', 
              'thenlper/gte-base', 
              'nomic-ai/nomic-embed-text-v1.5', 
              'nomic-ai/nomic-embed-text-v1.5-Q', 
              'nomic-ai/nomic-embed-text-v1', 
              'sentence-transformers/paraphrase-multilingual-mpnet-base-v2']
,

    "Sparse": ['prithivida/Splade_PP_en_v1', 
               'prithvida/Splade_PP_en_v1', 
               'Qdrant/bm42-all-minilm-l6-v2-attentions', 
               'Qdrant/bm25', 
               'Qdrant/minicoil-v1', 
               'naver/splade-cocondenser-ensembledistil', 
               'naver/splade-cocondenser-selfdistil', 
               'naver/efficient-splade-VI-BT-large-doc', 
               'naver/efficient-splade-VI-BT-large-query'],

    "Multi_vector": ['colbert-ir/colbertv2.0', 
                     'colbert-ir/colbert-v1.0', 
                     'jinaai/jina-colbert-v2']
}

models_semantic_splitting = {
            'sentence_transformers': [
                # Popular and efficient models
                'all-MiniLM-L6-v2',
                'all-mpnet-base-v2',
                'all-MiniLM-L12-v2',
                
                # Multilingual models
                'paraphrase-multilingual-MiniLM-L12-v2',
                'paraphrase-multilingual-mpnet-base-v2',
                
                # Specialized models
                'multi-qa-MiniLM-L6-cos-v1',
                'multi-qa-mpnet-base-cos-v1',
                'msmarco-distilbert-base-tas-b',
                
                # Latest high-performance models
                'BAAI/bge-small-en-v1.5',
                'BAAI/bge-base-en-v1.5',
                'BAAI/bge-large-en-v1.5',
                'mixedbread-ai/mxbai-embed-large-v1',
                'sentence-transformers/all-roberta-large-v1',
            ],
            'fastembed': [
                # BGE models (recommended)
                'BAAI/bge-small-en-v1.5',
                'BAAI/bge-base-en-v1.5',
                'BAAI/bge-large-en-v1.5',
                
                # Sentence Transformer equivalents
                'sentence-transformers/all-MiniLM-L6-v2',
                'sentence-transformers/all-MiniLM-L12-v2',
                'sentence-transformers/all-mpnet-base-v2',
                
                # Multilingual models
                'BAAI/bge-small-zh-v1.5',
                'BAAI/bge-base-zh-v1.5',
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                
                # Nomic models
                'nomic-ai/nomic-embed-text-v1',
                'nomic-ai/nomic-embed-text-v1.5',
                
                # Specialized models
                'sentence-transformers/multi-qa-MiniLM-L6-cos-v1',
                'microsoft/DialoGPT-medium',
            ]
        }

models_token_splitting = {
    "TIKTOKEN_MODELS" : {
        "cl100k_base": "cl100k_base",  
        "p50k_base": "p50k_base",      
        "p50k_edit": "p50k_edit",      
        "gpt2": "gpt2",                
        "r50k_base": "r50k_base",     
    },
    
    "HUGGINGFACE_MODELS" : {
        "gpt2": "gpt2",
        "gpt-neo-2.7b": "EleutherAI/gpt-neo-2.7B",
        "gpt-j-6b": "EleutherAI/gpt-j-6B",
        "opt-1.3b": "facebook/opt-1.3b",
        "flan-t5-base": "google/flan-t5-base",
        "bert-base": "bert-base-uncased",
        "roberta-base": "roberta-base",
        "distilbert-base": "distilbert-base-uncased",
        "codebert-base": "microsoft/codebert-base",
        "codet5-base": "Salesforce/codet5-base",
        "sentence-transformer": "sentence-transformers/all-MiniLM-L6-v2",
        "dialogpt-medium": "microsoft/DialoGPT-medium",
    }
}