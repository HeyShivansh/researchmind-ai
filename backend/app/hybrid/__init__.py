"""Hybrid retrieval subsystem for the ResearchMind AI platform.

Combines semantic search (Qdrant) and keyword search (BM25) using
Reciprocal Rank Fusion (RRF) into a single ranked result list.

    User Query
        ↓
    EmbeddingService → Semantic Search (Qdrant)
        +        ← Reciprocal Rank Fusion → Final Results
    BM25 Search (rank-bm25)
"""

from .exceptions import BM25IndexError, HybridRetrievalError
from .service import HybridRetrievalService

__all__ = [
    "BM25IndexError",
    "HybridRetrievalError",
    "HybridRetrievalService",
]
