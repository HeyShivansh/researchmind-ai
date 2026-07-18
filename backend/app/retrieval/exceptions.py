"""Domain exceptions for the retrieval subsystem.

Exception hierarchy::

    RetrievalError
    ├── QueryEmbeddingError
    ├── SemanticSearchError
    └── ChunkLookupError

Each exception translates a lower-layer failure into a meaningful
domain signal for the application layer.
"""

from __future__ import annotations


class RetrievalError(Exception):
    """Base exception for all retrieval-related errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class QueryEmbeddingError(RetrievalError):
    """Raised when the query embedding step fails.

    Wraps ``EmptyEmbeddingError`` or ``EmbeddingProviderError`` from
    the embedding subsystem.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SemanticSearchError(RetrievalError):
    """Raised when the Qdrant vector search step fails.

    Wraps ``SearchError`` from the vector store subsystem.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ChunkLookupError(RetrievalError):
    """Raised when the database chunk-lookup step fails.

    Wraps database-level errors from the repository layer.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
