"""Data models for the retrieval subsystem.

Uses ``dataclasses`` for lightweight, immutable, typed structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned to the application after semantic retrieval.

    Combines the vector-search score from Qdrant with the full chunk
    text from PostgreSQL into a single result object.

    Attributes
    ----------
    chunk_id : UUID
        The unique identifier of the chunk.
    paper_id : UUID
        The paper this chunk belongs to.
    text : str
        The full chunk text (from PostgreSQL).
    page_number : int
        1-based page number from the source document.
    chunk_index : int
        Global index of this chunk across the entire document (0-based).
    score : float
        Cosine similarity score from Qdrant (higher is more similar).
    """

    chunk_id: UUID
    paper_id: UUID
    text: str
    page_number: int
    chunk_index: int
    score: float
