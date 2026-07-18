"""Dependency injection package for the ResearchMind AI platform."""

from .database import get_db
from .services import (
    get_chunk_persistence_service,
    get_chunker,
    get_document_processor,
    get_embedding_provider,
    get_embedding_service,
    get_file_storage,
    get_hybrid_retrieval_service,
    get_paper_service,
    get_qdrant_client,
    get_qdrant_service,
    get_retrieval_service,
)

__all__ = [
    "get_chunk_persistence_service",
    "get_chunker",
    "get_db",
    "get_document_processor",
    "get_embedding_provider",
    "get_embedding_service",
    "get_file_storage",
    "get_hybrid_retrieval_service",
    "get_paper_service",
    "get_qdrant_client",
    "get_qdrant_service",
    "get_retrieval_service",
]
