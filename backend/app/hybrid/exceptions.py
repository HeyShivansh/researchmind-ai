"""Domain exceptions for the hybrid retrieval subsystem.

Exception hierarchy::

    HybridRetrievalError
    └── BM25IndexError
"""

from __future__ import annotations


class HybridRetrievalError(Exception):
    """Base exception for all hybrid-retrieval-related errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BM25IndexError(HybridRetrievalError):
    """Raised when building, rebuilding, or searching the BM25 index fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
