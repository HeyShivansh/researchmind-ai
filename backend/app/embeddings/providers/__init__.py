"""Concrete embedding provider implementations.

Each module in this package implements ``BaseEmbeddingProvider`` for a
specific embedding backend.

Initially, only ``gemini`` is implemented as a concrete provider.
``baai`` and ``ollama`` serve as placeholders for future integration.
"""

from .baai import BAAIEmbeddingProvider
from .gemini import GeminiEmbeddingProvider
from .ollama import OllamaEmbeddingProvider

__all__ = [
    "BAAIEmbeddingProvider",
    "GeminiEmbeddingProvider",
    "OllamaEmbeddingProvider",
]
