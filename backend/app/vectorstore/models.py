"""Data models for the vector store subsystem.

Uses ``dataclasses`` for lightweight, immutable, typed structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SearchResult:
    """A single result from a vector similarity search.

    The retrieval layer uses ``chunk_id`` to fetch the full chunk text
    from PostgreSQL — the vector store only stores vectors and
    lightweight metadata, not the text itself.

    Attributes
    ----------
    chunk_id : UUID
        The unique identifier of the matching chunk.
    score : float
        Cosine similarity score (higher is more similar).
    """

    chunk_id: UUID
    score: float
