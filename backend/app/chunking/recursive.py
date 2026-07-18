"""
Recursive character chunker implementation.

Splits documents into chunks by recursively trying different
separators (paragraph, sentence, word) and supports configurable
overlap for context preservation.
"""

from __future__ import annotations

from uuid import uuid4

from app.processing.models import ProcessedDocument

from .base import BaseChunker
from .exceptions import ChunkingError
from .models import DocumentChunk
from .utils import (
    SEPARATORS,
    apply_overlap,
    greedy_merge,
    recursive_split,
)


class RecursiveCharacterChunker(BaseChunker):
    """
    Chunker that recursively splits text using a separator hierarchy.

    After splitting, adjacent segments are greedily merged to maximise
    chunk utilisation.  Separators are preserved so concatenating
    chunks reproduces the original text exactly.

    Every produced ``DocumentChunk`` satisfies these invariants:

    - ``char_end > char_start``
    - ``char_count == len(text)``
    - ``char_end - char_start == len(text)``

    Parameters
    ----------
    chunk_size : int
        Maximum number of characters per chunk.
    chunk_overlap : int
        Number of overlapping characters between consecutive chunks
        within the same page.

    Raises
    ------
    ChunkingError
        If *chunk_size* is not greater than *chunk_overlap*.

    Examples
    --------
    >>> chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)
    >>> chunks = chunker.chunk(document)
    """

    def __init__(self, chunk_size: int, chunk_overlap: int = 0) -> None:
        if chunk_size <= chunk_overlap:
            raise ChunkingError(
                f"chunk_size ({chunk_size}) must be greater than "
                f"chunk_overlap ({chunk_overlap})"
            )
        if chunk_size <= 0:
            raise ChunkingError(
                f"chunk_size ({chunk_size}) must be positive"
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk(self, document: ProcessedDocument) -> list[DocumentChunk]:
        """
        Split a processed document into chunks.

        Each page is split independently, then chunks are assigned a
        global index across the entire document.

        Parameters
        ----------
        document : ProcessedDocument
            The processed PDF document to chunk.

        Returns
        -------
        list[DocumentChunk]
            Ordered list of chunks with unique IDs and page tracking.

        Raises
        ------
        ChunkingError
            If any chunk invariant is violated.
        """
        chunks: list[DocumentChunk] = []
        global_index = 0

        for page in document.pages:
            # 1. Recursive split — preserves separators.
            segments = recursive_split(page.text, self._chunk_size, SEPARATORS)
            # 2. Greedy merge — maximise chunk utilisation.
            merged = greedy_merge(segments, self._chunk_size)
            # 3. Internal consistency: merged chunks reconstruct the page.
            self._reconstruct_and_validate_from_tuples(merged, page.text)
            # 4. Overlap — with word-boundary awareness.
            overlapped = apply_overlap(
                page.text, merged, self._chunk_overlap
            )

            # Collect this page's chunks in a local list for validation.
            page_chunks: list[DocumentChunk] = []
            for chunk_text, char_start, char_end in overlapped:
                self._assert_chunk_invariants(
                    chunk_text, char_start, char_end
                )
                doc_chunk = DocumentChunk(
                    id=uuid4(),
                    page_number=page.page_number,
                    chunk_index=global_index,
                    text=chunk_text,
                    char_start=char_start,
                    char_end=char_end,
                    char_count=len(chunk_text),
                )
                page_chunks.append(doc_chunk)
                chunks.append(doc_chunk)
                global_index += 1

            # 5. Internal consistency: final chunk offsets are valid.
            self._validate_offsets(page_chunks, page.text)

        return chunks

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_chunk_invariants(
        text: str,
        char_start: int,
        char_end: int,
    ) -> None:
        """
        Verify that a chunk's fields satisfy internal consistency rules.

        Parameters
        ----------
        text : str
            The chunk text.
        char_start : int
            Start offset in the original page.
        char_end : int
            End offset in the original page.

        Raises
        ------
        ChunkingError
            If any invariant is violated.
        """
        if char_end <= char_start:
            raise ChunkingError(
                f"Chunk invariant violated: "
                f"char_end ({char_end}) must be > char_start ({char_start})"
            )
        if len(text) != char_end - char_start:
            raise ChunkingError(
                f"Chunk invariant violated: "
                f"len(text) ({len(text)}) must equal "
                f"char_end - char_start ({char_end - char_start})"
            )

    @staticmethod
    def _validate_offsets(
        chunks: list[DocumentChunk],
        original_text: str,
    ) -> None:
        """
        Validate that every chunk's offsets are valid substrings of the
        original text.

        Parameters
        ----------
        chunks : list[DocumentChunk]
            Chunks to validate.
        original_text : str
            The original page text.

        Raises
        ------
        ChunkingError
            If any chunk's offsets are invalid.
        """
        for chunk in chunks:
            if chunk.char_start < 0 or chunk.char_end > len(original_text):
                raise ChunkingError(
                    f"Chunk offsets ({chunk.char_start}, {chunk.char_end}) "
                    f"are outside page bounds [0, {len(original_text)}]"
                )
            if original_text[chunk.char_start:chunk.char_end] != chunk.text:
                raise ChunkingError(
                    f"Chunk text does not match original at offsets "
                    f"({chunk.char_start}, {chunk.char_end})"
                )

    @staticmethod
    def _reconstruct_and_validate_from_tuples(
        chunks: list[tuple[str, int, int]],
        original_text: str,
    ) -> None:
        """
        Verify that concatenating (non-overlap) chunk tuples reproduces
        the original page text.

        This is an internal consistency check only — it is not exposed
        publicly.

        Parameters
        ----------
        chunks : list[tuple[str, int, int]]
            Chunks as ``(text, start, end)`` tuples, before overlap.
        original_text : str
            The original page text.

        Raises
        ------
        ChunkingError
            If reconstruction does not match.
        """
        reconstructed = "".join(t[0] for t in chunks)
        if reconstructed != original_text:
            raise ChunkingError(
                "Reconstruction validation failed: concatenating chunks "
                "does not reproduce the original page text"
            )
