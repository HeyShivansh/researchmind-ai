"""Unit tests for the vector store subsystem.

Tests cover QdrantService with a fully mocked Qdrant client — no
real Qdrant server is required.  All Qdrant client calls are patched
at the method level.

Run with::

    uv run pytest tests/test_vectorstore.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from qdrant_client.http import models

from app.vectorstore import (
    CollectionError,
    DeleteError,
    QdrantService,
    SearchError,
    SearchResult,
    UpsertError,
    VectorStoreError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_client():
    """Provide a fully mocked QdrantClient."""
    return MagicMock(name="QdrantClient")


@pytest.fixture()
def service(mock_client) -> QdrantService:
    """Provide a QdrantService wired to the mocked client."""
    return QdrantService(
        client=mock_client,
        vector_dimension=4,
        collection_name="test-collection",
    )


# ===================================================================
# Collection management
# ===================================================================


class TestCollectionManagement:
    """Tests for ``QdrantService`` collection operations."""

    def test_create_collection(self, service: QdrantService, mock_client) -> None:
        """Verify ``create_collection`` creates when collection does not exist."""
        mock_client.collection_exists.return_value = False

        service.create_collection()

        mock_client.collection_exists.assert_called_once_with(
            collection_name="test-collection"
        )
        mock_client.create_collection.assert_called_once()

    def test_create_collection_skips_if_exists(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify ``create_collection`` is a no-op when collection exists."""
        mock_client.collection_exists.return_value = True

        service.create_collection()

        mock_client.create_collection.assert_not_called()

    def test_create_collection_uses_cosine_distance(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify the collection is created with cosine similarity."""
        mock_client.collection_exists.return_value = False

        service.create_collection()

        call_kwargs = mock_client.create_collection.call_args[1]
        vectors_config = call_kwargs["vectors_config"]
        assert vectors_config.distance == models.Distance.COSINE
        assert vectors_config.size == 4

    def test_create_collection_raises_on_failure(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify a provider failure raises ``CollectionError``."""
        mock_client.collection_exists.side_effect = RuntimeError("Connection refused")

        with pytest.raises(CollectionError, match="Failed to check"):
            service.create_collection()

    def test_collection_exists(self, service: QdrantService, mock_client) -> None:
        """Verify ``collection_exists`` returns the client's result."""
        mock_client.collection_exists.return_value = True

        assert service.collection_exists() is True
        mock_client.collection_exists.assert_called_once_with(
            collection_name="test-collection"
        )

    def test_collection_exists_raises_on_failure(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify ``collection_exists`` propagates errors as ``CollectionError``."""
        mock_client.collection_exists.side_effect = RuntimeError("Timeout")

        with pytest.raises(CollectionError, match="Timeout"):
            service.collection_exists()


# ===================================================================
# Single upsert
# ===================================================================


class TestSingleUpsert:
    """Tests for ``QdrantService.upsert_chunk``."""

    def test_upsert_single_chunk(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify a single chunk is upserted with the correct payload."""
        chunk_id = uuid4()
        paper_id = uuid4()
        vector = [0.1, 0.2, 0.3, 0.4]

        service.upsert_chunk(
            chunk_id=chunk_id,
            vector=vector,
            paper_id=paper_id,
            page_number=2,
            chunk_index=5,
        )

        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args[1]
        points = call_args["points"]
        assert len(points) == 1

        point = points[0]
        assert point.id == str(chunk_id)
        assert point.vector == vector
        assert point.payload["chunk_id"] == str(chunk_id)
        assert point.payload["paper_id"] == str(paper_id)
        assert point.payload["page_number"] == 2
        assert point.payload["chunk_index"] == 5

    def test_upsert_raises_on_failure(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify an upsert failure raises ``UpsertError``."""
        mock_client.upsert.side_effect = RuntimeError("Disk full")

        with pytest.raises(UpsertError, match="Disk full"):
            service.upsert_chunk(
                chunk_id=uuid4(),
                vector=[0.1, 0.2, 0.3, 0.4],
                paper_id=uuid4(),
                page_number=1,
                chunk_index=0,
            )


# ===================================================================
# Batch upsert
# ===================================================================


class TestBatchUpsert:
    """Tests for ``QdrantService.upsert_chunks``."""

    def test_upsert_multiple_chunks(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify multiple chunks are upserted in a single batch."""
        paper_id = uuid4()
        chunks = [
            (uuid4(), [0.1, 0.2, 0.3, 0.4], paper_id, 1, 0),
            (uuid4(), [0.5, 0.6, 0.7, 0.8], paper_id, 1, 1),
            (uuid4(), [0.9, 0.1, 0.2, 0.3], paper_id, 2, 2),
        ]

        service.upsert_chunks(chunks)

        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args[1]
        points = call_args["points"]
        assert len(points) == 3

        for point, (chunk_id, vector, _, page, index) in zip(
            points, chunks, strict=True
        ):
            assert point.id == str(chunk_id)
            assert point.vector == vector
            assert point.payload["page_number"] == page
            assert point.payload["chunk_index"] == index

    def test_upsert_empty_batch(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify an empty batch does not call the client."""
        service.upsert_chunks([])

        mock_client.upsert.assert_not_called()

    def test_upsert_batch_raises_on_failure(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify a batch failure raises ``UpsertError``."""
        mock_client.upsert.side_effect = RuntimeError("Batch failed")

        with pytest.raises(UpsertError, match="Batch failed"):
            service.upsert_chunks([
                (uuid4(), [0.1, 0.2, 0.3, 0.4], uuid4(), 1, 0),
            ])

    def test_upsert_uses_correct_collection(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify the upsert targets the configured collection."""
        chunk_id = uuid4()
        service.upsert_chunk(
            chunk_id=chunk_id,
            vector=[0.1, 0.2, 0.3, 0.4],
            paper_id=uuid4(),
            page_number=1,
            chunk_index=0,
        )

        call_kwargs = mock_client.upsert.call_args[1]
        assert call_kwargs["collection_name"] == "test-collection"


# ===================================================================
# Search
# ===================================================================


class TestSearch:
    """Tests for ``QdrantService.search``."""

    def test_search_returns_results(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify ``search`` returns ``SearchResult`` objects with correct data."""
        chunk_id_1 = uuid4()
        chunk_id_2 = uuid4()

        mock_client.query_points.return_value.points = [
            models.ScoredPoint(
                id=str(chunk_id_1),
                score=0.95,
                payload={
                    "chunk_id": str(chunk_id_1),
                    "paper_id": str(uuid4()),
                },
                version=1,
            ),
            models.ScoredPoint(
                id=str(chunk_id_2),
                score=0.87,
                payload={
                    "chunk_id": str(chunk_id_2),
                    "paper_id": str(uuid4()),
                },
                version=1,
            ),
        ]

        results = service.search([0.1, 0.2, 0.3, 0.4], limit=5)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].chunk_id == chunk_id_1
        assert results[0].score == 0.95
        assert results[1].chunk_id == chunk_id_2
        assert results[1].score == 0.87

    def test_search_passes_limit(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify the ``limit`` parameter is forwarded to the client."""
        mock_client.query_points.return_value.points = []

        service.search([0.1, 0.2, 0.3, 0.4], limit=3)

        mock_client.query_points.assert_called_once_with(
            collection_name="test-collection",
            query=[0.1, 0.2, 0.3, 0.4],
            limit=3,
        )

    def test_search_returns_empty_when_no_matches(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify search returns an empty list when there are no matches."""
        mock_client.query_points.return_value.points = []

        results = service.search([0.1, 0.2, 0.3, 0.4])

        assert results == []

    def test_search_raises_on_failure(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify a search failure raises ``SearchError``."""
        mock_client.query_points.side_effect = RuntimeError("Search timeout")

        with pytest.raises(SearchError, match="Search timeout"):
            service.search([0.1, 0.2, 0.3, 0.4])


# ===================================================================
# Delete by paper
# ===================================================================


class TestDeletePaper:
    """Tests for ``QdrantService.delete_paper``."""

    def test_delete_paper(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify ``delete_paper`` creates the correct filter."""
        paper_id = uuid4()

        service.delete_paper(paper_id)

        mock_client.delete.assert_called_once()
        call_kwargs = mock_client.delete.call_args[1]

        assert call_kwargs["collection_name"] == "test-collection"
        selector = call_kwargs["points_selector"]
        assert isinstance(selector, models.Filter)
        assert len(selector.must) == 1

        condition = selector.must[0]
        assert isinstance(condition, models.FieldCondition)
        assert condition.key == "paper_id"
        assert condition.match.value == str(paper_id)

    def test_delete_paper_raises_on_failure(
        self, service: QdrantService, mock_client
    ) -> None:
        """Verify a delete failure raises ``DeleteError``."""
        mock_client.delete.side_effect = RuntimeError("Delete failed")

        with pytest.raises(DeleteError, match="Delete failed"):
            service.delete_paper(uuid4())


# ===================================================================
# Exception hierarchy
# ===================================================================


class TestExceptionHierarchy:
    """Tests for the vector store exception hierarchy."""

    def test_all_caught_by_base(self) -> None:
        """Verify all custom exceptions can be caught as ``VectorStoreError``."""
        exceptions: list[VectorStoreError] = [
            CollectionError("msg"),
            UpsertError("msg"),
            SearchError("msg"),
            DeleteError("msg"),
        ]

        for exc in exceptions:
            assert isinstance(exc, VectorStoreError)
            assert isinstance(exc, Exception)

    def test_collection_error_has_name(self) -> None:
        """Verify ``CollectionError`` stores the collection name."""
        exc = CollectionError("fail", collection_name="my-collection")
        assert exc.collection_name == "my-collection"


# ===================================================================
# Properties
# ===================================================================


class TestProperties:
    """Tests for ``QdrantService`` property access."""

    def test_collection_name_property(self, service: QdrantService) -> None:
        """Verify ``collection_name`` returns the configured value."""
        assert service.collection_name == "test-collection"

    def test_vector_dimension_property(self, service: QdrantService) -> None:
        """Verify ``vector_dimension`` returns the configured value."""
        assert service.vector_dimension == 4
