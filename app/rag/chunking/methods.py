import re
from typing import List, Dict, Any, Optional
import tiktoken
import nltk
from sentence_transformers import SentenceTransformer
import sentence_transformers
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import fastembed
from fastembed import TextEmbedding
from transformers import AutoTokenizer
from app.rag.chunking.base import BaseChunker


class FixedSizeChunker(BaseChunker):
    """Splits text into fixed-size chunks based on character count."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100, **kwargs):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            if end < len(text) and not text[end].isspace():
                last_space = chunk.rfind(' ')
                if last_space > self.chunk_size * 0.5: 
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk]
    
class SentenceBasedChunker(BaseChunker):
    """Splits text by sentences using NLTK, with optional size limits."""
    
    def __init__(self, max_chunk_size: Optional[int] = None, **kwargs):
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        sentences = nltk.sent_tokenize(text)
        
        if self.max_chunk_size is None:
            return sentences
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
class SemanticChunker(BaseChunker):
    """Splits text based on semantic similarity between sentences."""

    def __init__(self,
                 embedding_model: str = 'all-MiniLM-L6-v2',
                 backend: str = 'sentence_transformers',
                 breakpoint_percentile: int = 90,
                 buffer_size: int = 1,
                 **kwargs):
        self.embedding_model = embedding_model
        self.backend = backend.lower()
        self.breakpoint_percentile = breakpoint_percentile
        self.buffer_size = buffer_size
        self._model = None
        
        if self.backend not in ['sentence_transformers', 'fastembed', 'auto']:
            raise ValueError(f"Unsupported backend: {self.backend}. Use 'sentence_transformers', 'fastembed', or 'auto'")
        
        self._check_backend_availability()

    def _check_backend_availability(self):
        """Check if the requested backend is available."""
        sentence_transformers_available = self._check_sentence_transformers()
        fastembed_available = self._check_fastembed()
        
        if self.backend == 'auto':
            if sentence_transformers_available:
                self.backend = 'sentence_transformers'
                print(f"Auto-selected backend: sentence_transformers")
            elif fastembed_available:
                self.backend = 'fastembed'
                print(f"Auto-selected backend: fastembed")
            else:
                raise ImportError("Neither sentence-transformers nor fastembed is available")
        
        elif self.backend == 'sentence_transformers' and not sentence_transformers_available:
            raise ImportError("sentence-transformers is not available. Install with: pip install sentence-transformers")
        
        elif self.backend == 'fastembed' and not fastembed_available:
            raise ImportError("fastembed is not available. Install with: pip install fastembed")

    def _check_sentence_transformers(self) -> bool:
        """Check if sentence-transformers is available."""
        try:
            import sentence_transformers
            return True
        except ImportError:
            return False

    def _check_fastembed(self) -> bool:
        """Check if fastembed is available."""
        try:
            import fastembed
            return True
        except ImportError:
            return False

    @property
    def model(self):
        """Load and cache the embedding model based on the selected backend."""
        if self._model is None:
            if self.backend == 'sentence_transformers':
                self._model = self._load_sentence_transformer_model()
            elif self.backend == 'fastembed':
                self._model = self._load_fastembed_model()
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
            
            print(f"Loaded model '{self.embedding_model}' using backend: {self.backend}")
        return self._model

    def _load_sentence_transformer_model(self):
        """Load a Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(self.embedding_model, trust_remote_code=True)
        except Exception as e:
            raise RuntimeError(f"Failed to load Sentence Transformer model '{self.embedding_model}': {e}")

    def _load_fastembed_model(self):
        """Load a FastEmbed model."""
        try:
            return TextEmbedding(model_name=self.embedding_model)
        except Exception as e:
            raise RuntimeError(f"Failed to load FastEmbed model '{self.embedding_model}': {e}")

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encode texts using the appropriate backend."""
        if self.backend == 'sentence_transformers':
            return self.model.encode(texts)
        elif self.backend == 'fastembed':
            embeddings = list(self.model.embed(texts))
            return np.array(embeddings)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def combine_sentences(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine sentences with their neighbors for better context."""
        for i, sentence in enumerate(sentences):
            combined_sentence = " ".join(
                sentences[j]['sentence']
                for j in range(i - self.buffer_size, i + self.buffer_size + 1)
                if 0 <= j < len(sentences)
            )
            sentence['combined_sentence'] = combined_sentence
        return sentences

    def calculate_cosine_distances(self, sentences: List[Dict[str, Any]]) -> List[float]:
        """Calculate cosine distances between adjacent sentence embeddings."""
        distances = []
        for i in range(len(sentences) - 1):
            dist = 1 - cosine_similarity(
                [sentences[i]['combined_sentence_embedding']],
                [sentences[i + 1]['combined_sentence_embedding']]
            )[0][0]
            distances.append(dist)
        return distances

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []

        sentence_texts = re.split(r'(?<=[.?!])\s+', text)
        sentence_texts = [s.strip() for s in sentence_texts if s.strip()]

        if len(sentence_texts) <= 1:
            return [text]

        sentences = [{'sentence': sent, 'index': i} for i, sent in enumerate(sentence_texts)]
        sentences = self.combine_sentences(sentences)

        combined_sentences = [s['combined_sentence'] for s in sentences]
        embeddings = self._encode_texts(combined_sentences)
        
        for i, sentence in enumerate(sentences):
            sentence['combined_sentence_embedding'] = embeddings[i]

        distances = self.calculate_cosine_distances(sentences)
        breakpoint_threshold = np.percentile(distances, self.breakpoint_percentile)

        chunks = []
        start_index = 0

        for i, distance in enumerate(distances):
            if distance > breakpoint_threshold:
                chunk_text = ' '.join([s['sentence'] for s in sentences[start_index:i + 1]])
                chunks.append(chunk_text)
                start_index = i + 1

        if start_index < len(sentences):
            chunk_text = ' '.join([s['sentence'] for s in sentences[start_index:]])
            chunks.append(chunk_text)

        return [chunk for chunk in chunks if chunk.strip()]

    @staticmethod
    def get_available_models() -> Dict[str, List[str]]:
        """Get available models for each backend."""
        models = {
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
        return models
    
class SlidingWindowChunker(BaseChunker):
    """Creates overlapping chunks using a sliding window approach."""
    
    def __init__(self, 
                 window_size: int = 1000,
                 step_size: int = 500,
                 unit: str = 'char',  # 'char', 'word', 'sentence'
                 **kwargs):
        self.window_size = window_size
        self.step_size = step_size
        self.unit = unit
    
    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        if self.unit == 'char':
            return self._chunk_by_char(text)
        elif self.unit == 'word':
            return self._chunk_by_word(text)
        elif self.unit == 'sentence':
            return self._chunk_by_sentence(text)
        else:
            raise ValueError(f"Unsupported unit: {self.unit}")
    
    def _chunk_by_char(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.step_size):
            chunk = text[i:i + self.window_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks
    
    def _chunk_by_word(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.step_size):
            chunk_words = words[i:i + self.window_size]
            chunk = ' '.join(chunk_words)
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        sentences = nltk.sent_tokenize(text)
        chunks = []
        
        for i in range(0, len(sentences), self.step_size):
            chunk_sentences = sentences[i:i + self.window_size]
            chunk = ' '.join(chunk_sentences)
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks

class TokenBasedChunker:
    """Splits text based on token count using various tokenizer models."""
    
    # Supported model mappings
    TIKTOKEN_MODELS = {
        "cl100k_base": "cl100k_base",  # GPT-4, GPT-3.5, text-embedding-ada-002
        "p50k_base": "p50k_base",      # GPT-3 models
        "p50k_edit": "p50k_edit",      # Codex models
        "gpt2": "gpt2",                # GPT-2
        "r50k_base": "r50k_base",      # GPT-1
    }
    
    HUGGINGFACE_MODELS = {
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
    
    def __init__(self,
                 token_size: int = 500,
                 token_overlap: int = 50,
                 model_name: str = "cl100k_base",
                 tokenizer_backend: str = "auto",  # "tiktoken", "huggingface", "auto"
                 **kwargs):
        """
        Initialize the TokenBasedChunker.
        
        Args:
            token_size: Maximum tokens per chunk
            token_overlap: Number of overlapping tokens between chunks
            model_name: Name of the tokenizer model to use
            tokenizer_backend: Backend to use ("tiktoken", "huggingface", "auto")
        """
        self.token_size = token_size
        self.token_overlap = token_overlap
        self.model_name = model_name
        self.tokenizer_backend = tokenizer_backend
        self.tokenizer = None
        self._setup_tokenizer()
    
    def _setup_tokenizer(self):
        """Setup the appropriate tokenizer based on model and backend."""
        if self.tokenizer_backend == "auto":
            # Try tiktoken first, then huggingface
            if self.model_name in self.TIKTOKEN_MODELS:
                self.tokenizer_backend = "tiktoken"
            elif self.model_name in self.HUGGINGFACE_MODELS:
                self.tokenizer_backend = "huggingface"
            else:
                # Default to tiktoken if model name is not in our mappings
                self.tokenizer_backend = "tiktoken"
        
        try:
            if self.tokenizer_backend == "tiktoken":
                self._setup_tiktoken()
            elif self.tokenizer_backend == "huggingface":
                self._setup_huggingface()
            else:
                raise ValueError(f"Unsupported tokenizer backend: {self.tokenizer_backend}")
        except Exception as e:
            # Fallback to tiktoken with cl100k_base
            self.tokenizer_backend = "tiktoken"
            self.model_name = "cl100k_base"
            self._setup_tiktoken()
    
    def _setup_tiktoken(self):
        """Setup tiktoken tokenizer."""
        try:
            encoding_name = self.TIKTOKEN_MODELS.get(self.model_name, self.model_name)
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            # Fallback to cl100k_base
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _setup_huggingface(self):
        """Setup Hugging Face tokenizer."""
        try:
            model_path = self.HUGGINGFACE_MODELS.get(self.model_name, self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            # Handle tokenizers without pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            raise RuntimeError(f"Failed to load Hugging Face model {self.model_name}: {e}")
    
    def _encode_text(self, text: str) -> List[int]:
        """Encode text to tokens based on tokenizer backend."""
        if self.tokenizer_backend == "tiktoken":
            return self.tokenizer.encode(text)
        elif self.tokenizer_backend == "huggingface":
            return self.tokenizer.encode(text, add_special_tokens=False)
        else:
            raise ValueError(f"Unsupported tokenizer backend: {self.tokenizer_backend}")
    
    def _decode_tokens(self, tokens: List[int]) -> str:
        """Decode tokens to text based on tokenizer backend."""
        if self.tokenizer_backend == "tiktoken":
            return self.tokenizer.decode(tokens)
        elif self.tokenizer_backend == "huggingface":
            return self.tokenizer.decode(tokens, skip_special_tokens=True)
        else:
            raise ValueError(f"Unsupported tokenizer backend: {self.tokenizer_backend}")
    
    def chunk(self, text: str) -> List[str]:
        """
        Split text into chunks based on token count.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        try:
            tokens = self._encode_text(text)
            chunks = []
            
            for i in range(0, len(tokens), self.token_size - self.token_overlap):
                chunk_tokens = tokens[i:i + self.token_size]
                chunk_text = self._decode_tokens(chunk_tokens).strip()
                if chunk_text:
                    chunks.append(chunk_text)
            
            return chunks
        
        except Exception as e:
            # Fallback to simple character-based chunking
            return self._fallback_chunk(text)
    
    def _fallback_chunk(self, text: str) -> List[str]:
        """Fallback chunking method using character approximation."""
        # Rough approximation: 1 token ≈ 4 characters
        char_size = self.token_size * 4
        char_overlap = self.token_overlap * 4
        
        chunks = []
        for i in range(0, len(text), char_size - char_overlap):
            chunk = text[i:i + char_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def get_token_count(self, text: str) -> int:
        """Get the token count for a given text."""
        try:
            return len(self._encode_text(text))
        except Exception:
            # Fallback approximation
            return len(text) // 4
    
    @classmethod
    def list_available_models(cls) -> dict:
        """List all available models by backend."""
        return {
            "tiktoken": list(cls.TIKTOKEN_MODELS.keys()),
            "huggingface": list(cls.HUGGINGFACE_MODELS.keys())
        }

class RecursiveCharacterChunker(BaseChunker):
    """Recursively splits text using different separators."""
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 100, 
                 separators: Optional[List[str]] = None, 
                 **kwargs):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
    
    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        final_chunks = []
        
        def _recursive_split(text: str, separators: List[str]):
            if not text or not separators:
                if text:
                    final_chunks.append(text.strip())
                return
            
            separator = ""
            for s in separators:
                if s in text:
                    separator = s
                    break
            
            if not separator:
                if len(text) <= self.chunk_size:
                    final_chunks.append(text.strip())
                else:
                    for i in range(0, len(text), self.chunk_size):
                        chunk = text[i:i + self.chunk_size]
                        if chunk.strip():
                            final_chunks.append(chunk.strip())
                return
            
            splits = text.split(separator)
            current_chunk = ""
            
            for i, split in enumerate(splits):
                test_chunk = current_chunk + separator + split if current_chunk else split
                
                if len(test_chunk) <= self.chunk_size:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        final_chunks.append(current_chunk.strip())
                    
                    if len(split) > self.chunk_size:
                        _recursive_split(split, separators[1:])
                    else:
                        current_chunk = split
            
            if current_chunk:
                final_chunks.append(current_chunk.strip())
        
        _recursive_split(text, self.separators)
        return [chunk for chunk in final_chunks if chunk]

class HybridChunker(BaseChunker):
    """Combines semantic chunking with token-based splitting for optimal results."""
    
    def __init__(self, 
                 token_size: int = 512,
                 embedding_model: str = 'all-MiniLM-L6-v2',
                 breakpoint_percentile: int = 90,
                 buffer_size: int = 1,
                 model_name: str = "cl100k_base",
                 **kwargs):
        
        self.semantic_chunker = SemanticChunker(
            embedding_model=embedding_model,
            breakpoint_percentile=breakpoint_percentile,
            buffer_size=buffer_size
        )
        
        self.token_chunker = TokenBasedChunker(
            token_size=token_size,
            token_overlap=50,
            model_name=model_name
        )
        
        self.token_size = token_size
        self.tokenizer = tiktoken.get_encoding(model_name)
    
    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        semantic_chunks = self.semantic_chunker.chunk(text)
        
        final_chunks = []
        
        for chunk in semantic_chunks:
            chunk_tokens = len(self.tokenizer.encode(chunk))
            
            if chunk_tokens <= self.token_size:
                final_chunks.append(chunk)
            else:
                token_sub_chunks = self.token_chunker.chunk(chunk)
                final_chunks.extend(token_sub_chunks)
        
        return final_chunks

def get_chunker(strategy_config: Dict[str, Any]) -> BaseChunker:
    """Factory function to create chunker based on strategy configuration."""
    
    strategy_name = strategy_config.get("strategy", "hybrid").lower()
    
    print(f"Initializing chunker with strategy: {strategy_name}")
    
    chunker_map = {
        "fixed_size": FixedSizeChunker,
        "sentence_based": SentenceBasedChunker,
        "semantic_based": SemanticChunker,
        "sliding_window": SlidingWindowChunker,
        "token_based": TokenBasedChunker,
        "hybrid": HybridChunker,
        "recursive": RecursiveCharacterChunker,
    }
    
    chunker_class = chunker_map.get(strategy_name)
    
    if chunker_class is None:
        available_strategies = list(chunker_map.keys())
        raise NotImplementedError(
            f"Chunking strategy '{strategy_name}' not implemented. "
            f"Available strategies: {available_strategies}"
        )
    
    config = {k: v for k, v in strategy_config.items() if k != 'strategy'}
    
    return chunker_class(**config)
