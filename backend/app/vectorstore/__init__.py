"""Vector store subsystem for the ResearchMind AI platform.

Provides a lightweight Qdrant-backed vector store for embedding
vectors.  PostgreSQL remains the source of truth for chunk text;
Qdrant stores only vectors and minimal metadata.

The subsystem is organised into:

- ``models`` — Immutable dataclasses (``SearchResult``)
- ``exceptions`` — Domain exception hierarchy
- ``service`` — ``QdrantService`` (the sole component for Qdrant interaction)
"""

from .exceptions import (
    CollectionError,
    DeleteError,
    SearchError,
    UpsertError,
    VectorStoreError,
)
from .models import SearchResult
from .service import QdrantService

__all__ = [
    "CollectionError",
    "DeleteError",
    "QdrantService",
    "SearchError",
    "SearchResult",
    "UpsertError",
    "VectorStoreError",
]
