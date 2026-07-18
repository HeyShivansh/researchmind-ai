"""Domain exceptions for the vector store subsystem.

Exception hierarchy::

    VectorStoreError
    ├── CollectionError
    ├── UpsertError
    ├── SearchError
    └── DeleteError
"""

from __future__ import annotations


class VectorStoreError(Exception):
    """Base exception for all vector-store-related errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CollectionError(VectorStoreError):
    """Raised when collection creation or existence check fails."""

    def __init__(
        self, message: str, *, collection_name: str | None = None
    ) -> None:
        self.collection_name = collection_name
        super().__init__(message)


class UpsertError(VectorStoreError):
    """Raised when point upsertion fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchError(VectorStoreError):
    """Raised when vector search fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DeleteError(VectorStoreError):
    """Raised when point deletion fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
