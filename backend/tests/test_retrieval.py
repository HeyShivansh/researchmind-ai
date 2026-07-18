"""Unit tests for the retrieval subsystem.

Tests cover RetrievalService with fully mocked EmbeddingService,
QdrantService, and ChunkRepository — no real services are required.

Run with::

    uv run pytest tests/test_retrieval.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.embeddings import EmbeddingResult
from app.embeddings.exceptions import EmbeddingProviderError, EmptyEmbeddingError
from app.retrieval import (
    ChunkLookupError,
    QueryEmbeddingError,
    RetrievalError,
    RetrievalService,
    RetrievedChunk,
    SemanticSearchError,
)
from app.vectorstore import SearchResult
from app.vectorstore.exceptions import SearchError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_embedding_service():
    """Provide a mocked EmbeddingService."""
    svc = MagicMock(name="EmbeddingService")
    svc.embed_text.return_value = EmbeddingResult(
        vector=[0.1, 0.2, 0.3, 0.4],
        model_name="test-model",
        dimension=4,
    )
    return svc


@pytest.fixture()
def mock_qdrant_service():
    """Provide a mocked QdrantService."""
    return MagicMock(name="QdrantService")


@pytest.fixture()
def mock_chunk_repository():
    """Provide a mocked ChunkRepository."""
    return MagicMock(name="ChunkRepository")


@pytest.fixture()
def retrieval_service(
    mock_embedding_service,
    mock_qdrant_service,
    mock_chunk_repository,
) -> RetrievalService:
    """Provide a RetrievalService wired to mocked dependencies."""
    return RetrievalService(
        embedding_service=mock_embedding_service,
        qdrant_service=mock_qdrant_service,
        chunk_repository=mock_chunk_repository,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_orm_chunk(
    chunk_id: UUID,
    paper_id: UUID,
    text: str = "Some chunk text",
    page_number: int = 1,
    chunk_index: int = 0,
):
    """Build a minimal mock ORM chunk object.

    ``ChunkRepository.get_by_ids`` returns real ``PaperChunk`` ORM
    instances.  We simulate them with a simple object that has the
    attributes that ``RetrievalService`` accesses.
    """
    obj = MagicMock(name="PaperChunk")
    obj.id = chunk_id
    obj.paper_id = paper_id
    obj.text = text
    obj.page_number = page_number
    obj.chunk_index = chunk_index
    return obj


# ===================================================================
# Successful retrieval
# ===================================================================


class TestSuccessfulRetrieval:
    """Tests for the happy path."""

    def test_returns_retrieved_chunks(
        self, retrieval_service: RetrievalService, mock_qdrant_service, mock_chunk_repository
    ) -> None:
        """Verify a successful retrieval returns ``RetrievedChunk`` objects."""
        paper_id = uuid4()
        chunk_id_1 = uuid4()
        chunk_id_2 = uuid4()

        mock_qdrant_service.search.return_value = [
            SearchResult(chunk_id=chunk_id_1, score=0.95),
            SearchResult(chunk_id=chunk_id_2, score=0.87),
        ]
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(chunk_id_1, paper_id, text="Chunk A", page_number=1, chunk_index=0),
            _make_orm_chunk(chunk_id_2, paper_id, text="Chunk B", page_number=2, chunk_index=1),
        ]

        results = retrieval_service.semantic_search("test query", top_k=2)

        assert len(results) == 2
        assert isinstance(results[0], RetrievedChunk)
        assert isinstance(results[1], RetrievedChunk)

    def test_correct_data_in_results(
        self, retrieval_service: RetrievalService, mock_qdrant_service, mock_chunk_repository
    ) -> None:
        """Verify all fields are populated correctly."""
        paper_id = uuid4()
        chunk_id = uuid4()

        mock_qdrant_service.search.return_value = [
            SearchResult(chunk_id=chunk_id, score=0.95),
        ]
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(
                chunk_id, paper_id,
                text="Chunk text content",
                page_number=3,
                chunk_index=7,
            ),
        ]

        results = retrieval_service.semantic_search("test query", top_k=1)
        result = results[0]

        assert result.chunk_id == chunk_id
        assert result.paper_id == paper_id
        assert result.text == "Chunk text content"
        assert result.page_number == 3
        assert result.chunk_index == 7
        assert result.score == 0.95

    def test_results_ordered_by_score(
        self, retrieval_service: RetrievalService, mock_qdrant_service, mock_chunk_repository
    ) -> None:
        """Verify results are ordered from highest to lowest score."""
        paper_id = uuid4()
        ids = [uuid4(), uuid4(), uuid4()]
        scores = [0.95, 0.87, 0.72]

        mock_qdrant_service.search.return_value = [
            SearchResult(chunk_id=ids[0], score=scores[0]),
            SearchResult(chunk_id=ids[1], score=scores[1]),
            SearchResult(chunk_id=ids[2], score=scores[2]),
        ]
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(ids[i], paper_id, text=f"Chunk {i}", chunk_index=i)
            for i in range(3)
        ]

        results = retrieval_service.semantic_search("test query", top_k=3)

        assert [r.score for r in results] == [0.95, 0.87, 0.72]

    def test_embed_query_works(
        self, retrieval_service: RetrievalService, mock_embedding_service
    ) -> None:
        """Verify ``embed_query`` returns the embedding result."""
        result = retrieval_service.embed_query("test query")

        assert isinstance(result, EmbeddingResult)
        assert result.vector == [0.1, 0.2, 0.3, 0.4]

    def test_no_search_results(
        self, retrieval_service: RetrievalService, mock_qdrant_service
    ) -> None:
        """Verify an empty Qdrant result returns an empty list."""
        mock_qdrant_service.search.return_value = []

        results = retrieval_service.semantic_search("test query")

        assert results == []


# ===================================================================
# Validation
# ===================================================================


class TestValidation:
    """Tests for input validation."""

    def test_empty_query_raises_error(
        self, retrieval_service: RetrievalService
    ) -> None:
        """Verify an empty query raises ``QueryEmbeddingError``."""
        with pytest.raises(QueryEmbeddingError, match="empty"):
            retrieval_service.semantic_search("")

    def test_whitespace_query_raises_error(
        self, retrieval_service: RetrievalService
    ) -> None:
        """Verify a whitespace-only query raises ``QueryEmbeddingError``."""
        with pytest.raises(QueryEmbeddingError, match="empty"):
            retrieval_service.semantic_search("   \t\n  ")

    def test_non_positive_top_k_raises_error(
        self, retrieval_service: RetrievalService
    ) -> None:
        """Verify ``top_k=0`` raises ``RetrievalError``."""
        with pytest.raises(RetrievalError, match="top_k must be positive"):
            retrieval_service.semantic_search("test query", top_k=0)

    def test_negative_top_k_raises_error(
        self, retrieval_service: RetrievalService
    ) -> None:
        """Verify ``top_k=-1`` raises ``RetrievalError``."""
        with pytest.raises(RetrievalError, match="top_k must be positive"):
            retrieval_service.semantic_search("test query", top_k=-1)


# ===================================================================
# Embedding failures
# ===================================================================


class TestEmbeddingFailures:
    """Tests for query embedding failure handling."""

    def test_empty_embedding_propagates(
        self, retrieval_service: RetrievalService, mock_embedding_service
    ) -> None:
        """Verify an empty-query embedding failure raises ``QueryEmbeddingError``."""
        # Service validates input before calling embedder, so this
        # tests the embed_query method directly.
        mock_embedding_service.embed_text.side_effect = EmptyEmbeddingError("empty")

        with pytest.raises(QueryEmbeddingError, match="empty"):
            retrieval_service.embed_query("")

    def test_embedding_provider_failure(
        self, retrieval_service: RetrievalService, mock_embedding_service
    ) -> None:
        """Verify an embedding provider failure raises ``QueryEmbeddingError``."""
        mock_embedding_service.embed_text.side_effect = EmbeddingProviderError(
            "API error", provider_name="gemini"
        )

        with pytest.raises(QueryEmbeddingError, match="Failed to embed"):
            retrieval_service.semantic_search("test query")

    def test_embed_query_raises_on_empty(
        self, retrieval_service: RetrievalService, mock_embedding_service
    ) -> None:
        """Verify ``embed_query`` raises ``QueryEmbeddingError`` for empty input."""
        mock_embedding_service.embed_text.side_effect = EmptyEmbeddingError("empty")

        # The service validates before calling, so the error comes
        # from the embedder for this path
        with pytest.raises(QueryEmbeddingError):
            retrieval_service.embed_query("")


# ===================================================================
# Vector search failures
# ===================================================================


class TestVectorSearchFailures:
    """Tests for Qdrant search failure handling."""

    def test_search_failure(
        self, retrieval_service: RetrievalService, mock_qdrant_service
    ) -> None:
        """Verify a Qdrant search failure raises ``SemanticSearchError``."""
        mock_qdrant_service.search.side_effect = SearchError("Qdrant timeout")

        with pytest.raises(SemanticSearchError, match="Qdrant timeout"):
            retrieval_service.semantic_search("test query")


# ===================================================================
# Chunk lookup failures
# ===================================================================


class TestChunkLookupFailures:
    """Tests for database chunk-lookup failure handling."""

    def test_chunk_lookup_failure(
        self, retrieval_service: RetrievalService, mock_qdrant_service, mock_chunk_repository
    ) -> None:
        """Verify a database failure raises ``ChunkLookupError``."""
        mock_qdrant_service.search.return_value = [
            SearchResult(chunk_id=uuid4(), score=0.9),
        ]
        mock_chunk_repository.get_by_ids.side_effect = RuntimeError("DB connection lost")

        with pytest.raises(ChunkLookupError, match="Failed to look up"):
            retrieval_service.semantic_search("test query")


# ===================================================================
# Missing chunks
# ===================================================================


class TestMissingChunks:
    """Tests for handling chunks not found in the database."""

    def test_missing_chunks_skipped(
        self, retrieval_service: RetrievalService, mock_qdrant_service, mock_chunk_repository
    ) -> None:
        """Verify chunks missing from the DB are safely skipped."""
        paper_id = uuid4()
        chunk_id_1 = uuid4()
        chunk_id_2 = uuid4()

        mock_qdrant_service.search.return_value = [
            SearchResult(chunk_id=chunk_id_1, score=0.95),
            SearchResult(chunk_id=chunk_id_2, score=0.87),
        ]
        # Only return the second chunk — first is missing
        mock_chunk_repository.get_by_ids.return_value = [
            _make_orm_chunk(chunk_id_2, paper_id, text="Chunk B"),
        ]

        results = retrieval_service.semantic_search("test query", top_k=2)

        assert len(results) == 1
        assert results[0].chunk_id == chunk_id_2
        assert results[0].score == 0.87


# ===================================================================
# Exception hierarchy
# ===================================================================


class TestExceptionHierarchy:
    """Tests for the retrieval exception hierarchy."""

    def test_all_caught_by_base(self) -> None:
        """Verify all custom exceptions can be caught as ``RetrievalError``."""
        exceptions: list[RetrievalError] = [
            QueryEmbeddingError("msg"),
            SemanticSearchError("msg"),
            ChunkLookupError("msg"),
        ]

        for exc in exceptions:
            assert isinstance(exc, RetrievalError)
            assert isinstance(exc, Exception)
