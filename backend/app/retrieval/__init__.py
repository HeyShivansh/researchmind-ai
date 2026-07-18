"""Semantic retrieval subsystem for the ResearchMind AI platform.

Provides a pure semantic retrieval pipeline:

    User Query
        ↓
    EmbeddingService.embed_text()
        ↓
    QdrantService.search()
        ↓
    ChunkRepository.get_by_ids()
        ↓
    RetrievedChunk

No BM25, no reranking, no LLM — just vector similarity retrieval.
"""

from .exceptions import (
    ChunkLookupError,
    QueryEmbeddingError,
    RetrievalError,
    SemanticSearchError,
)
from .models import RetrievedChunk
from .service import RetrievalService

__all__ = [
    "ChunkLookupError",
    "QueryEmbeddingError",
    "RetrievalError",
    "RetrievalService",
    "RetrievedChunk",
    "SemanticSearchError",
]
