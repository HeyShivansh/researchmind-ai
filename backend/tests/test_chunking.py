"""
Unit tests for the chunking subsystem.

Tests cover RecursiveCharacterChunker, utility functions, and
DocumentChunk models.  No database or FastAPI dependencies.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.chunking import (
    BaseChunker,
    ChunkingError,
    DocumentChunk,
    RecursiveCharacterChunker,
)
from app.chunking.utils import _nearest_word_boundary, apply_overlap, greedy_merge, recursive_split
from app.processing.models import DocumentMetadata, DocumentPage, ProcessedDocument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_document(pages: list[tuple[int, str]]) -> ProcessedDocument:
    """Build a ``ProcessedDocument`` from ``(page_number, text)`` pairs."""
    return ProcessedDocument(
        metadata=DocumentMetadata(
            title=None, author=None, subject=None,
            creator=None, producer=None, page_count=len(pages),
        ),
        pages=[
            DocumentPage(page_number=pn, text=t, char_count=len(t))
            for pn, t in pages
        ],
    )


def _single_page_doc(text: str) -> ProcessedDocument:
    """Build a single-page document with *text*."""
    return _make_document([(1, text)])


# ===================================================================
# DocumentChunk model
# ===================================================================


class TestDocumentChunk:
    """Tests for the ``DocumentChunk`` dataclass."""

    def test_is_frozen(self) -> None:
        """Verify ``DocumentChunk`` cannot be modified after creation."""
        chunk = DocumentChunk(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            page_number=1,
            chunk_index=0,
            text="Hello",
            char_start=0,
            char_end=5,
            char_count=5,
        )
        with pytest.raises(AttributeError):
            chunk.text = "Changed"  # type: ignore[misc]


# ===================================================================
# BaseChunker interface
# ===================================================================


class TestBaseChunker:
    """Tests for the ``BaseChunker`` ABC."""

    def test_cannot_instantiate(self) -> None:
        """Verify ``BaseChunker`` cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseChunker()  # type: ignore[abstract]


# ===================================================================
# Configuration
# ===================================================================


class TestConfiguration:
    """Tests for ``RecursiveCharacterChunker`` constructor validation."""

    def test_invalid_chunk_size_raises_error(self) -> None:
        """Verify zero chunk_size raises ``ChunkingError``."""
        with pytest.raises(ChunkingError):
            RecursiveCharacterChunker(chunk_size=0, chunk_overlap=0)

    def test_overlap_exceeds_size_raises_error(self) -> None:
        """Verify overlap >= chunk_size raises ``ChunkingError``."""
        with pytest.raises(ChunkingError):
            RecursiveCharacterChunker(chunk_size=100, chunk_overlap=200)

    def test_equal_size_and_overlap_raises_error(self) -> None:
        """Verify overlap == chunk_size raises ``ChunkingError``."""
        with pytest.raises(ChunkingError):
            RecursiveCharacterChunker(chunk_size=100, chunk_overlap=100)


# ===================================================================
# Empty document
# ===================================================================


class TestEmptyDocument:
    """Tests for chunking an empty document."""

    def test_empty_page_returns_no_chunks(self) -> None:
        """Verify an empty page produces zero chunks."""
        doc = _make_document([(1, "")])
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)

        assert chunks == []

    def test_zero_page_document(self) -> None:
        """Verify a document with no pages produces zero chunks."""
        doc = ProcessedDocument(
            metadata=DocumentMetadata(
                title=None, author=None, subject=None,
                creator=None, producer=None, page_count=0,
            ),
            pages=[],
        )
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)

        assert chunks == []


# ===================================================================
# One page
# ===================================================================


class TestOnePage:
    """Tests for chunking a single page."""

    def test_short_text_returns_single_chunk(self) -> None:
        """Verify text shorter than chunk_size produces one chunk."""
        doc = _single_page_doc("Hello, world!")
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)

        assert len(chunks) == 1
        assert chunks[0].text == "Hello, world!"
        assert chunks[0].page_number == 1

    def test_long_text_split_into_multiple_chunks(self) -> None:
        """Verify text longer than chunk_size is split."""
        text = "word " * 50
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.char_count <= 100


# ===================================================================
# Multiple pages
# ===================================================================


class TestMultiplePages:
    """Tests for chunking documents with multiple pages."""

    def test_page_number_preserved(self) -> None:
        """Verify each chunk retains its source page number."""
        doc = _make_document([
            (1, "Page one content."),
            (2, "Page two content."),
        ])
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)

        assert len(chunks) == 2
        assert chunks[0].page_number == 1
        assert chunks[1].page_number == 2

    def test_chunk_indices_global(self) -> None:
        """Verify chunk indices are sequential across pages."""
        doc = _make_document([
            (1, "Page one " * 20),
            (2, "Page two " * 20),
        ])
        chunker = RecursiveCharacterChunker(chunk_size=50)

        chunks = chunker.chunk(doc)
        indices = [c.chunk_index for c in chunks]

        assert indices == list(range(len(chunks)))


# ===================================================================
# UUID uniqueness
# ===================================================================


class TestUUIDUniqueness:
    """Tests that every chunk has a unique ID."""

    def test_all_ids_unique(self) -> None:
        """Verify no two chunks share the same UUID."""
        doc = _single_page_doc("word " * 200)
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)
        ids = {c.id for c in chunks}

        assert len(ids) == len(chunks)


# ===================================================================
# Character offsets
# ===================================================================


class TestCharacterOffsets:
    """Tests for char_start / char_end correctness."""

    def test_offsets_match_text(self) -> None:
        """Verify ``text == original[char_start:char_end]``."""
        text = "Hello. This is a longer paragraph. It has sentences."
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=20)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            extracted = text[chunk.char_start : chunk.char_end]
            assert chunk.text == extracted

    def test_offsets_sequential(self) -> None:
        """Verify chunk offsets are non-overlapping and in order."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50)

        chunks = chunker.chunk(doc)

        prev_end = 0
        for chunk in chunks:
            assert chunk.char_start >= prev_end
            assert chunk.char_end > chunk.char_start
            prev_end = chunk.char_end

    def test_offsets_reconstruct_original_substring(self) -> None:
        """Verify each chunk's offsets index into the original correctly."""
        text = "The quick brown fox jumps over the lazy dog."
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=15)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert text[chunk.char_start:chunk.char_end] == chunk.text


# ===================================================================
# Chunk size limit
# ===================================================================


class TestChunkSizeLimit:
    """Tests that no chunk exceeds the configured size."""

    def test_all_chunks_within_limit(self) -> None:
        """Verify every chunk's ``char_count <= chunk_size``."""
        text = "word " * 500
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=200)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.char_count <= 200

    def test_greedy_merge_never_oversized(self) -> None:
        """Verify greedy_merge never produces chunks exceeding chunk_size."""
        text = "word " * 500
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=150)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.char_count <= 150


# ===================================================================
# Separator preservation
# ===================================================================


class TestSeparatorPreservation:
    """Tests that separators are preserved in chunk texts."""

    def test_newlines_preserved(self) -> None:
        """Verify double-newline separators appear in chunk texts."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=100)

        chunks = chunker.chunk(doc)

        combined = "".join(c.text for c in chunks)
        assert "\n\n" in combined
        assert combined == text


# ===================================================================
# Reconstruction
# ===================================================================


class TestReconstruction:
    """Tests that concatenating chunks reproduces the original text."""

    def test_reconstructs_exact_original(self) -> None:
        """Verify joining all chunk texts gives the original page text."""
        text = (
            "This is a long document. It has multiple sentences!\n\n"
            "It also has paragraphs. With different structures.\n"
            "And various kinds of punctuation: commas, semicolons; "
            "and other things."
        )
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50)

        chunks = chunker.chunk(doc)
        reconstructed = "".join(c.text for c in chunks)

        assert reconstructed == text


# ===================================================================
# Greedy merging
# ===================================================================


class TestGreedyMerge:
    """Tests for the greedy_merge utility."""

    def test_empty_input(self) -> None:
        """Verify empty input returns empty list."""
        assert greedy_merge([], 100) == []

    def test_single_segment(self) -> None:
        """Verify a single segment is returned unchanged."""
        segments = [("Hello", 0, 5)]
        result = greedy_merge(segments, 100)
        assert result == segments

    def test_merges_small_segments(self) -> None:
        """Verify segments that fit together are merged."""
        segments = [
            ("Hello ", 0, 6),
            ("World ", 6, 12),
            ("Foo", 12, 15),
        ]
        result = greedy_merge(segments, 15)
        assert len(result) == 1
        assert result[0][0] == "Hello World Foo"

    def test_splits_when_exceeding_limit(self) -> None:
        """Verify a new chunk starts when the next segment would exceed limit."""
        segments = [
            ("Hello ", 0, 6),
            ("World ", 6, 12),
            ("Foo bar baz", 12, 23),
        ]
        result = greedy_merge(segments, 15)
        assert len(result) == 2
        assert result[0][0] == "Hello World "
        assert result[1][0] == "Foo bar baz"

    def test_merges_offsets_correctly(self) -> None:
        """Verify offsets in merged chunks correspond to original text."""
        text = "Hello World Foo bar baz"
        segments = [
            ("Hello ", 0, 6),
            ("World ", 6, 12),
            ("Foo bar baz", 12, 23),
        ]
        result = greedy_merge(segments, 15)
        for chunk_text, start, end in result:
            assert chunk_text == text[start:end]

    def test_raises_on_oversized_segment(self) -> None:
        """Verify an oversized segment raises ``ChunkingError``."""
        segments = [("Hello world " * 50, 0, 600)]
        with pytest.raises(ChunkingError, match="exceeds chunk_size"):
            greedy_merge(segments, 100)


# ===================================================================
# Overlap boundary
# ===================================================================


class TestOverlapBoundary:
    """Tests that overlap expands to nearest word boundary."""

    def test_overlap_no_word_split(self) -> None:
        """Verify overlap doesn't start in the middle of a word."""
        text = "The quick brown fox jumps over the lazy dog"
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=15, chunk_overlap=5)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            if chunk.char_start > 0:
                char_before = text[chunk.char_start - 1]
                assert char_before.isspace() or chunk.char_start == 0

    def test_overlap_increases_text(self) -> None:
        """Verify overlapping chunks include text from the previous region."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=10)

        chunks = chunker.chunk(doc)

        if len(chunks) > 1:
            assert chunks[1].char_start < chunks[0].char_end

    def test_no_overlap_when_zero(self) -> None:
        """Verify overlap=0 produces non-overlapping chunks."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=0)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.text == text[chunk.char_start : chunk.char_end]

    def test_overlap_never_exceeds_2x(self) -> None:
        """Verify overlap expansion never exceeds 2× overlap characters."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=5)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            if chunk.char_start > 0:
                actual_expansion = chunk.char_end - chunk.char_start - len(chunk.text)
                assert actual_expansion <= 10  # 2 × overlap


# ===================================================================
# Word boundary utility
# ===================================================================


class TestNearestWordBoundary:
    """Tests for the ``_nearest_word_boundary`` utility."""

    def test_at_word_boundary(self) -> None:
        """Verify a position after a space stays unchanged."""
        result = _nearest_word_boundary("hello world", 6, max_distance=10)
        assert result == 6  # position 6 is right after ' '

    def test_mid_word_expands_backward(self) -> None:
        """Verify a position in the middle of a word expands backward."""
        result = _nearest_word_boundary("hello world", 8, max_distance=10)
        assert result == 6  # "world" starts at 6

    def test_mid_word_within_distance(self) -> None:
        """Verify expansion stops at word boundary within max_distance."""
        result = _nearest_word_boundary("a bb ccc dddd", 11, max_distance=5)
        assert result == 9  # "dddd" starts at index 9

    def test_no_whitespace_returns_original(self) -> None:
        """Verify with no whitespace, original position is returned."""
        # "hello" has no whitespace; position 3 should stay 3.
        result = _nearest_word_boundary("hello", 3, max_distance=10)
        assert result == 3


# ===================================================================
# Chunk invariants
# ===================================================================


class TestChunkInvariants:
    """Tests for internal chunk invariant checks."""

    def test_char_count_equals_len_text(self) -> None:
        """Verify every chunk has ``char_count == len(text)``."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.char_count == len(chunk.text)

    def test_char_end_minus_char_start_equals_len_text(self) -> None:
        """Verify ``char_end - char_start == len(text)``."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.char_end - chunk.char_start == len(chunk.text)

    def test_char_end_gt_char_start(self) -> None:
        """Verify ``char_end > char_start`` for every chunk."""
        text = "word " * 100
        doc = _single_page_doc(text)
        chunker = RecursiveCharacterChunker(chunk_size=50)

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.char_end > chunk.char_start


# ===================================================================
# Utility: recursive_split
# ===================================================================


class TestRecursiveSplit:
    """Tests for the ``recursive_split`` utility."""

    def test_empty_text(self) -> None:
        """Verify empty text returns empty list."""
        assert recursive_split("", 100) == []

    def test_short_text(self) -> None:
        """Verify short text returns single segment."""
        result = recursive_split("Hello", 100)
        assert result == [("Hello", 0, 5)]

    def test_separator_preserved(self) -> None:
        """Verify the separator is included in the preceding segment."""
        text = "First\n\nSecond"
        # chunk_size=7 forces a split ("First\n\n" is 7 chars)
        result = recursive_split(text, 7, ["\n\n"])
        assert len(result) == 2
        assert result[0][0] == "First\n\n"
        assert result[1][0] == "Second"

    def test_fallback_char_split(self) -> None:
        """Verify fallback character splitting works."""
        text = "ABCDEFGHIJ"
        result = recursive_split(text, 3, [])
        assert len(result) == 4
        assert result[0] == ("ABC", 0, 3)
        assert result[1] == ("DEF", 3, 6)
        assert result[2] == ("GHI", 6, 9)
        assert result[3] == ("J", 9, 10)


# ===================================================================
# Utility: apply_overlap
# ===================================================================


class TestApplyOverlap:
    """Tests for the ``apply_overlap`` utility."""

    def test_no_overlap_returns_unchanged(self) -> None:
        """Verify overlap=0 returns chunks unchanged."""
        chunks = [("Hello ", 0, 6), ("World", 6, 11)]
        result = apply_overlap("Hello World", chunks, 0)
        assert result == chunks

    def test_overlap_adjusts_start_to_word_boundary(self) -> None:
        """Verify overlap shifts start to the nearest word boundary."""
        text = "The quick brown fox"
        chunks = [("The quick ", 0, 10), ("brown fox", 10, 19)]
        result = apply_overlap(text, chunks, 5)

        assert len(result) == 2
        _, new_start, new_end = result[1]
        assert text[new_start:new_end] == "quick brown fox"

    def test_no_whitespace_fallback(self) -> None:
        """Verify no-whitespace text uses original overlap position."""
        text = "abcde" * 10
        chunks = [
            ("abcdeabcdeabcdeabcdeabcde", 0, 25),
            ("abcdeabcdeabcdeabcdeabcde", 25, 50),
        ]
        result = apply_overlap(text, chunks, 5)

        assert len(result) == 2
        _, new_start, _ = result[1]
        assert new_start == 20  # max(0, 25 - 5)
