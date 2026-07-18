"""Unit tests for the hybrid retrieval subsystem.

Tests cover HybridRetrievalService with mocked RetrievalService and
ChunkRepository — no real Qdrant or database connections required.
BM25 is exercised through rank-bm25 on small synthetic data.

Run with::

    uv run pytest tests/test_hybrid.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.hybrid import BM25IndexError, HybridRetrievalError, HybridRetrievalService
from app.retrieval.models import RetrievedChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(
    chunk_id: UUID | None = None,
    paper_id: UUID | None = None,
    text: str = "Some chunk text",
    page_number: int = 1,
    chunk_index: int = 0,
    score: float = 0.5,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id or uuid4(),
        paper_id=paper_id or uuid4(),
        text=text,
        page_number=page_number,
        chunk_index=chunk_index,
        score=score,
    )


def _make_orm_row(chunk_id: UUID, text: str):
    """Build a minimal mock object simulating a DB row with .id and .text."""
    row = MagicMock(name="Row")
    row.id = chunk_id
    row.text = text
    return row


def _make_orm_chunk(chunk_id: UUID, paper_id: UUID, text: str):
    """Build a minimal mock ORM chunk (simulates PaperChunk)."""
    obj = MagicMock(name="PaperChunk")
    obj.id = chunk_id
    obj.paper_id = paper_id
    obj.text = text
    obj.page_number = 1
    obj.chunk_index = 0
    return obj


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_retrieval_service():
    """Provide a mocked RetrievalService."""
    return MagicMock(name="RetrievalService")


@pytest.fixture()
def mock_chunk_repository():
    """Provide a mocked ChunkRepository."""
    return MagicMock(name="ChunkRepository")


@pytest.fixture()
def hybrid_service(
    mock_retrieval_service,
    mock_chunk_repository,
) -> HybridRetrievalService:
    """Provide a HybridRetrievalService wired to mocked dependencies."""
    return HybridRetrievalService(
        retrieval_service=mock_retrieval_service,
        chunk_repository=mock_chunk_repository,
        semantic_top_k=5,
        keyword_top_k=5,
        fusion_k=60,
    )


# ===================================================================
# BM25 index building
# ===================================================================


class TestBM25Index:
    """Tests for BM25 index building."""

    def test_rebuild_index(
        self, hybrid_service: HybridRetrievalService, mock_chunk_repository
    ) -> None:
        """Verify ``rebuild_index`` fetches texts and builds the index."""
        chunk_id = uuid4()
        mock_chunk_repository.get_all_texts.return_value = [
            (chunk_id, "the quick brown fox"),
        ]

        hybrid_service.rebuild_index()

        assert hybrid_service._bm25 is not None
        assert hybrid_service._bm25_ids == [chunk_id]

    def test_rebuild_index_empty(
        self, hybrid_service: HybridRetrievalService, mock_chunk_repository
    ) -> None:
        """Verify an empty corpus produces no index."""
        mock_chunk_repository.get_all_texts.return_value = []

        hybrid_service.rebuild_index()

        assert hybrid_service._bm25 is None
        assert hybrid_service._bm25_ids == []

    def test_rebuild_index_raises_on_failure(
        self, hybrid_service: HybridRetrievalService, mock_chunk_repository
    ) -> None:
        """Verify a DB failure raises ``BM25IndexError``."""
        mock_chunk_repository.get_all_texts.side_effect = RuntimeError("DB down")

        with pytest.raises(BM25IndexError, match="Failed to fetch"):
            hybrid_service.rebuild_index()


# ===================================================================
# Semantic search
# ===================================================================


class TestSemanticSearch:
    """Tests for delegated semantic search."""

    def test_delegates_to_retrieval_service(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service
    ) -> None:
        """Verify ``semantic_search`` delegates to the injected service."""
        expected = [_make_chunk()]
        mock_retrieval_service.semantic_search.return_value = expected

        results = hybrid_service.semantic_search("test query")

        mock_retrieval_service.semantic_search.assert_called_once_with(
            "test query", top_k=5
        )
        assert results == expected

    def test_uses_custom_top_k(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service
    ) -> None:
        """Verify a custom ``top_k`` override is passed through."""
        mock_retrieval_service.semantic_search.return_value = []

        hybrid_service.semantic_search("test query", top_k=20)

        mock_retrieval_service.semantic_search.assert_called_once_with(
            "test query", top_k=20
        )


# ===================================================================
# Keyword search (BM25)
# ===================================================================


class TestKeywordSearch:
    """Tests for BM25 keyword search."""

    def test_keyword_search_returns_results(
        self, hybrid_service: HybridRetrievalService, mock_chunk_repository
    ) -> None:
        """Verify BM25 search returns correctly ordered results."""
        chunk_id_1 = uuid4()
        chunk_id_2 = uuid4()
        chunk_id_3 = uuid4()
        # Use 3+ documents so IDF is non-zero (rank-bm25 gives IDF=0
        # when a term appears in exactly half the corpus).
        mock_chunk_repository.get_all_texts.return_value = [
            (chunk_id_1, "fox dog rabbit"),
            (chunk_id_2, "cat fish bird"),
            (chunk_id_3, "elephant giraffe lion"),
        ]
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(chunk_id_1, uuid4(), "fox dog rabbit"),
            _make_orm_chunk(chunk_id_2, uuid4(), "cat fish bird"),
            _make_orm_chunk(chunk_id_3, uuid4(), "elephant giraffe lion"),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.keyword_search("fox dog")

        # Only the matching chunk has a non-zero score; non-matching chunks
        # are filtered out.
        assert len(results) == 1
        assert results[0].chunk_id == chunk_id_1  # "fox" + "dog" both match chunk 1
        assert results[0].score > 0

    def test_keyword_search_no_match(
        self, hybrid_service: HybridRetrievalService, mock_chunk_repository
    ) -> None:
        """Verify BM25 with no matches returns empty list."""
        mock_chunk_repository.get_all_texts.return_value = [
            (uuid4(), "some completely unrelated text"),
            (uuid4(), "also unrelated content"),
            (uuid4(), "more unrelated words here"),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.keyword_search("zzzzzzzz")

        assert results == []

    def test_keyword_search_empty_index(
        self, hybrid_service: HybridRetrievalService, mock_chunk_repository
    ) -> None:
        """Verify keyword search with no index returns empty list."""
        mock_chunk_repository.get_all_texts.return_value = []
        results = hybrid_service.keyword_search("test")
        assert results == []


# ===================================================================
# Hybrid search (RRF fusion)
# ===================================================================


class TestHybridSearch:
    """Tests for the full hybrid search pipeline."""

    def test_hybrid_search_uses_both_methods(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service, mock_chunk_repository
    ) -> None:
        """Verify ``hybrid_search`` calls both semantic and keyword search."""
        chunk_id = uuid4()
        mock_chunk_repository.get_all_texts.return_value = [
            (chunk_id, "attention mechanism transformer"),
        ]
        mock_retrieval_service.semantic_search.return_value = [
            _make_chunk(chunk_id, text="attention mechanism transformer", score=0.9),
        ]
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(chunk_id, uuid4(), "attention mechanism transformer"),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.hybrid_search("attention", top_k=5)

        assert len(results) == 1
        assert mock_retrieval_service.semantic_search.called

    def test_semantic_only_result(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service, mock_chunk_repository
    ) -> None:
        """Verify a chunk found only by semantic search still appears."""
        chunk_id = uuid4()
        mock_chunk_repository.get_all_texts.return_value = [
            (uuid4(), "completely unrelated"),
        ]
        mock_retrieval_service.semantic_search.return_value = [
            _make_chunk(chunk_id, text="unique semantic result", score=0.8),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.hybrid_search("test query", top_k=5)

        assert len(results) == 1
        assert results[0].chunk_id == chunk_id
        assert results[0].score > 0  # RRF score > 0

    def test_keyword_only_result(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service, mock_chunk_repository
    ) -> None:
        """Verify a chunk found only by keyword search still appears."""
        chunk_id = uuid4()
        # Use 3 documents so IDF is non-zero for the matching term.
        mock_chunk_repository.get_all_texts.return_value = [
            (chunk_id, "unique keyword match here"),
            (uuid4(), "completely unrelated text one"),
            (uuid4(), "completely unrelated text two"),
        ]
        mock_retrieval_service.semantic_search.return_value = []
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(chunk_id, uuid4(), "unique keyword match here"),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.hybrid_search("keyword match", top_k=5)

        assert len(results) == 1
        assert results[0].chunk_id == chunk_id

    def test_overlapping_result_gets_higher_score(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service, mock_chunk_repository
    ) -> None:
        """Verify a chunk in both result sets gets a higher fused score."""
        semantic_only = uuid4()
        keyword_only = uuid4()
        overlap = uuid4()
        paper_id = uuid4()

        mock_chunk_repository.get_all_texts.return_value = [
            (keyword_only, "python programming language"),
            (overlap, "machine learning algorithms"),
            (uuid4(), "completely unrelated text here"),
        ]
        mock_retrieval_service.semantic_search.return_value = [
            _make_chunk(semantic_only, paper_id, text="semantic result", score=0.9),
            _make_chunk(overlap, paper_id, text="machine learning algorithms", score=0.85),
        ]
        mock_chunk_repository.get_by_ids.side_effect = lambda ids: [
            _make_orm_chunk(keyword_only, paper_id, "python programming language"),
            _make_orm_chunk(overlap, paper_id, "machine learning algorithms"),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.hybrid_search("machine learning python", top_k=5)

        # The overlap chunk should have the highest RRF score
        overlap_result = [r for r in results if r.chunk_id == overlap]
        assert len(overlap_result) == 1
        # The overlap chunk should rank higher than either non-overlapping result
        assert results[0].chunk_id == overlap

    def test_rrf_ordering(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service, mock_chunk_repository
    ) -> None:
        """Verify RRF ordering is deterministic and score-based."""
        ids = [uuid4(), uuid4(), uuid4()]
        paper_id = uuid4()

        mock_chunk_repository.get_all_texts.return_value = [
            (ids[0], "dog cat"),
            (ids[1], "bird fish"),
            (ids[2], "cat dog"),
        ]
        mock_retrieval_service.semantic_search.return_value = [
            _make_chunk(ids[0], paper_id, text="dog cat", score=0.9),
            _make_chunk(ids[1], paper_id, text="bird fish", score=0.7),
        ]
        mock_chunk_repository.get_by_ids.side_effect = lambda ids: [
            _make_orm_chunk(ids[0], paper_id, "dog cat"),
            _make_orm_chunk(ids[1], paper_id, "bird fish"),
            _make_orm_chunk(ids[2], paper_id, "cat dog"),
        ]

        hybrid_service.rebuild_index()
        results = hybrid_service.hybrid_search("cat dog", top_k=5)

        # Run twice to verify determinism
        results_2 = hybrid_service.hybrid_search("cat dog", top_k=5)
        assert [r.chunk_id for r in results] == [r.chunk_id for r in results_2]

        # Scores should be descending
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_no_results(
        self, hybrid_service: HybridRetrievalService, mock_retrieval_service, mock_chunk_repository
    ) -> None:
        """Verify hybrid search with no matches returns empty list."""
        mock_chunk_repository.get_all_texts.return_value = [
            (uuid4(), "unrelated text"),
        ]
        mock_retrieval_service.semantic_search.return_value = []

        hybrid_service.rebuild_index()
        results = hybrid_service.hybrid_search("zzzzzzzzz", top_k=5)

        assert results == []


# ===================================================================
# Validation
# ===================================================================


class TestValidation:
    """Tests for input validation."""

    def test_empty_query_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        """Verify an empty query raises ``HybridRetrievalError``."""
        with pytest.raises(HybridRetrievalError, match="empty"):
            hybrid_service.hybrid_search("")

    def test_whitespace_query_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        """Verify a whitespace-only query raises ``HybridRetrievalError``."""
        with pytest.raises(HybridRetrievalError, match="empty"):
            hybrid_service.hybrid_search("   \t\n  ")

    def test_non_positive_top_k_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        """Verify ``top_k=0`` raises ``HybridRetrievalError``."""
        with pytest.raises(HybridRetrievalError, match="top_k must be positive"):
            hybrid_service.hybrid_search("test", top_k=0)

    def test_negative_top_k_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        """Verify ``top_k=-1`` raises ``HybridRetrievalError``."""
        with pytest.raises(HybridRetrievalError, match="top_k must be positive"):
            hybrid_service.hybrid_search("test", top_k=-1)


# ===================================================================
# Exception hierarchy
# ===================================================================


class TestExceptionHierarchy:
    """Tests for the hybrid retrieval exception hierarchy."""

    def test_bm25_error_caught_by_base(self) -> None:
        """Verify ``BM25IndexError`` can be caught as ``HybridRetrievalError``."""
        exc = BM25IndexError("index failed")
        assert isinstance(exc, HybridRetrievalError)
        assert isinstance(exc, Exception)
