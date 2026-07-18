"""
Data models for document chunking.

Uses ``dataclasses`` for lightweight, immutable, typed structures
that represent the output of the chunking subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DocumentChunk:
    """
    A single chunk of text extracted from a processed document page.

    Attributes
    ----------
    id : UUID
        Unique identifier for this chunk.
    page_number : int
        1-based page number from the source document.
    chunk_index : int
        Global index of this chunk across the entire document (0-based).
    text : str
        The chunk content.
    char_start : int
        Starting character offset within the original page text.
    char_end : int
        Ending character offset (exclusive) within the original page text.
    char_count : int
        Number of characters in this chunk's text.
    """

    id: UUID
    page_number: int
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    char_count: int
