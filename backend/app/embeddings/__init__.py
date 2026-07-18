"""Embedding subsystem for the ResearchMind AI platform.

Provides a provider-agnostic embedding abstraction that supports
multiple embedding providers without changing business logic.

The subsystem is organised into:

- ``base`` — Abstract base provider (``BaseEmbeddingProvider``)
- ``models`` — Immutable dataclasses (``EmbeddingResult``)
- ``service`` — Orchestration layer (``EmbeddingService``)
- ``exceptions`` — Domain exception hierarchy
- ``providers`` — Concrete provider implementations
"""

from .base import BaseEmbeddingProvider
from .exceptions import (
    BatchEmbeddingError,
    EmbeddingDimensionError,
    EmbeddingError,
    EmbeddingProviderError,
    EmptyEmbeddingError,
)
from .models import EmbeddingResult
from .service import EmbeddingService

__all__ = [
    "BaseEmbeddingProvider",
    "BatchEmbeddingError",
    "EmbeddingDimensionError",
    "EmbeddingError",
    "EmbeddingProviderError",
    "EmbeddingResult",
    "EmbeddingService",
    "EmptyEmbeddingError",
]
