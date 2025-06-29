from abc import ABC, abstractmethod
from typing import List

class BaseChunker(ABC):
    """Abstract base class for all chunking strategies."""
    
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass