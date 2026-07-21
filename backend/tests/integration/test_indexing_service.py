"""Integration tests for the DocumentIndexingService and the upload-to-index pipeline.

Verifies that the upload pipeline automatically indexes chunks into Qdrant
via the DocumentIndexingService.  No manual embedding or Qdrant upsert calls
are needed — the PaperService handles it.

Run with::

    uv run pytest tests/integration/test_indexing_service.py -v
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import fitz
import pytest
from sqlalchemy.orm import Session

from app.embeddings import EmbeddingService
from app.models.paper_chunk import PaperChunk
from app.repositories.paper_repository import PaperRepository
from app.services.chunk_persistence_service import ChunkPersistenceService
from app.services.indexing_service import DocumentIndexingError, DocumentIndexingService
from app.services.paper_service import PaperService
from app.storage.file_storage import FileStorage
from app.vectorstore import QdrantService

# ---------------------------------------------------------------------------
# Test PDF content
# ---------------------------------------------------------------------------

PAGE_1_TEXT: str = (
    "Artificial Intelligence is transforming healthcare. "
    "Machine learning assists doctors with diagnosis."
)

PAGE_2_TEXT: str = (
    "Qdrant is a vector database used for semantic search. "
    "BM25 improves keyword retrieval. "
    "Hybrid retrieval combines semantic and lexical search."
)


def _create_test_pdf(path: Path) -> Path:
    """Create a 2-page test PDF with predefined content."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(fitz.Point(72, 72), PAGE_1_TEXT, fontsize=11)
    page2 = doc.new_page()
    page2.insert_text(fitz.Point(72, 72), PAGE_2_TEXT, fontsize=11)
    doc.set_metadata({"title": "Integration Test Paper"})
    doc.save(str(path))
    doc.close()
    return path


def _upload_pdf(
    paper_service: PaperService,
    pdf_bytes: bytes,
    title: str = "Integration Test Paper",
):
    """Upload a PDF and return the created Paper record."""
    return paper_service.upload_paper(
        file_bytes=pdf_bytes,
        filename="test.pdf",
        title=title,
    )


def _count_qdrant_points_for_paper(
    qdrant_service: QdrantService,
    paper_id: UUID,
) -> int:
    """Count the number of Qdrant points belonging to a specific paper.

    Uses the Qdrant scroll API via the client to count points
    matching the given paper_id.
    """
    try:
        points = qdrant_service._client.scroll(
            collection_name=qdrant_service.collection_name,
            limit=10000,
        )[0]
    except Exception:
        return 0
    return sum(
        1 for p in points
        if p.payload.get("paper_id") == str(paper_id)
    )


# ===================================================================
# Test 1: Upload automatically indexes into Qdrant
# ===================================================================


class TestAutomaticIndexingDuringUpload:
    """Verify that upload automatically indexes chunks into Qdrant."""

    def test_upload_inserts_vectors_into_qdrant(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        qdrant_service: QdrantService,
        chunk_persistence_service: ChunkPersistenceService,
    ) -> None:
        """Verify that after upload, Qdrant contains vectors for the paper."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_pdf(paper_service, pdf.read_bytes())

        num_vectors = _count_qdrant_points_for_paper(qdrant_service, paper.id)
        assert num_vectors >= 1, (
            f"Expected at least 1 vector in Qdrant for paper {paper.id}, "
            f"got {num_vectors}"
        )

    def test_number_of_vectors_equals_number_of_chunks(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        qdrant_service: QdrantService,
        chunk_persistence_service: ChunkPersistenceService,
    ) -> None:
        """Verify that every chunk has a corresponding vector in Qdrant."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_pdf(paper_service, pdf.read_bytes())

        chunks = chunk_persistence_service.list_chunks(paper.id)
        num_chunks = len(chunks)

        num_vectors = _count_qdrant_points_for_paper(qdrant_service, paper.id)

        assert num_vectors == num_chunks, (
            f"Expected {num_chunks} vectors in Qdrant for paper {paper.id}, "
            f"got {num_vectors}"
        )

    def test_semantic_search_returns_results_after_upload(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
        chunk_persistence_service: ChunkPersistenceService,
    ) -> None:
        """Verify that semantic search returns at least one result after upload."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_pdf(paper_service, pdf.read_bytes())

        chunks = chunk_persistence_service.list_chunks(paper.id)

        # Use a chunk's text to embed and search
        query_embedding = embedding_service.embed_text(chunks[0].text)
        results = qdrant_service.search(
            vector=query_embedding.vector,
            limit=10,
        )

        assert len(results) >= 1, (
            "Semantic search should return at least 1 result after upload"
        )


# ===================================================================
# Test 2: Rollback on indexing failure
# ===================================================================


class TestRollbackOnIndexingFailure:
    """Verify that if indexing fails, the database and filesystem are rolled back."""

    def test_rollback_occurs_if_embedding_fails(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        qdrant_service: QdrantService,
        db_session: Session,
        tmp_storage: FileStorage,
    ) -> None:
        """Verify that DB and file are rolled back when embedding fails.

        When the embedding service raises an exception, the upload
        transaction must be rolled back (no paper record, no chunks)
        and the uploaded PDF must be deleted from storage.
        """
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        pdf_bytes = pdf.read_bytes()
        file_size = len(pdf_bytes)

        # Mock the embedding service to fail inside the indexing service
        with patch.object(
            paper_service._indexing_service._embedding_service,
            "embed_batch",
            side_effect=RuntimeError("Simulated embedding failure"),
        ):
            with pytest.raises(DocumentIndexingError, match="Simulated embedding failure"):
                _upload_pdf(paper_service, pdf_bytes)

        # Verify no paper record was left in the database
        repo = PaperRepository(db_session)
        all_papers = repo.list(limit=100)
        matching = [p for p in all_papers if p.title == "Integration Test Paper"]
        assert len(matching) == 0, (
            f"Expected no paper record to remain after rollback, "
            f"but found {len(matching)}"
        )

        # Verify the PDF files on disk: the rollback should have removed them.
        # We saved the file under a UUID-based name, which has no title
        # reference visible from the file name.  The simplest check is that
        # the total number of files in storage is what it was before.
        storage_dir = tmp_storage.root / "papers"
        if storage_dir.is_dir():
            remaining_files = list(storage_dir.iterdir())
            # A rollback deletes the PDF via FileStorage.delete_pdf,
            # so there should be no files left (test dir is empty before).
            assert len(remaining_files) == 0, (
                f"Expected 0 files in storage after rollback, "
                f"but found {len(remaining_files)}: {[f.name for f in remaining_files]}"
            )

    def test_qdrant_has_no_points_after_embedding_failure(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        qdrant_service: QdrantService,
    ) -> None:
        """Verify that no Qdrant points remain from a failed upload.

        Since the embedding service fails before Qdrant upsert is called,
        the Qdrant collection should have the same number of points
        before and after the attempted upload.
        """
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        pdf_bytes = pdf.read_bytes()

        # Count all points currently in Qdrant
        initial_points = qdrant_service._client.scroll(
            collection_name=qdrant_service.collection_name,
            limit=10000,
        )[0]
        initial_count = len(initial_points)

        # Mock the embedding service to fail
        with patch.object(
            paper_service._indexing_service._embedding_service,
            "embed_batch",
            side_effect=RuntimeError("Simulated embedding failure"),
        ):
            with pytest.raises(DocumentIndexingError):
                _upload_pdf(paper_service, pdf_bytes)

        # The embedding fails before upsert, so no new points are added
        after_points = qdrant_service._client.scroll(
            collection_name=qdrant_service.collection_name,
            limit=10000,
        )[0]
        after_count = len(after_points)

        assert after_count == initial_count, (
            f"Expected {initial_count} Qdrant points after rollback, "
            f"but found {after_count}"
        )

    def test_rollback_occurs_if_qdrant_upsert_fails(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        qdrant_service: QdrantService,
        db_session: Session,
    ) -> None:
        """Verify that DB and file are rolled back when Qdrant upsert fails.

        If embedding succeeds but the Qdrant upsert fails, the database
        transaction must be rolled back and the PDF deleted.
        """
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        pdf_bytes = pdf.read_bytes()

        # Mock the Qdrant upsert to fail after embedding succeeds
        with patch.object(
            qdrant_service,
            "upsert_chunks",
            side_effect=RuntimeError("Simulated Qdrant upsert failure"),
        ):
            with pytest.raises(DocumentIndexingError, match="Simulated Qdrant upsert failure"):
                _upload_pdf(paper_service, pdf_bytes)

        # Verify no paper record was left in the database
        repo = PaperRepository(db_session)
        all_papers = repo.list(limit=100)
        matching = [p for p in all_papers if p.title == "Integration Test Paper"]
        assert len(matching) == 0, (
            f"Expected no paper record to remain after rollback, "
            f"but found {len(matching)}"
        )


# ===================================================================
# Test 3: DocumentIndexingService unit tests
# ===================================================================


class TestDocumentIndexingServiceUnit:
    """Unit-level tests for the DocumentIndexingService."""

    def test_index_document_empty_chunks(
        self,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
    ) -> None:
        """Verify that indexing with empty chunks returns 0 and does nothing."""
        service = DocumentIndexingService(
            embedding_service=embedding_service,
            qdrant_service=qdrant_service,
        )
        result = service.index_document(
            paper_id=UUID("00000000-0000-0000-0000-000000000001"),
            chunks=[],
        )
        assert result == 0

    def test_index_document_raises_on_embedding_failure(
        self,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
    ) -> None:
        """Verify that an embedding failure raises DocumentIndexingError."""
        service = DocumentIndexingService(
            embedding_service=embedding_service,
            qdrant_service=qdrant_service,
        )

        chunk = PaperChunk(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            paper_id=UUID("00000000-0000-0000-0000-000000000002"),
            text="test text",
            page_number=1,
            chunk_index=0,
            char_start=0,
            char_end=9,
            char_count=9,
        )

        with patch.object(
            embedding_service,
            "embed_batch",
            side_effect=RuntimeError("Embedding failed"),
        ):
            with pytest.raises(DocumentIndexingError, match="Embedding failed"):
                service.index_document(
                    paper_id=UUID("00000000-0000-0000-0000-000000000002"),
                    chunks=[chunk],
                )

    def test_index_document_raises_on_upsert_failure(
        self,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
    ) -> None:
        """Verify that a Qdrant upsert failure raises DocumentIndexingError."""
        service = DocumentIndexingService(
            embedding_service=embedding_service,
            qdrant_service=qdrant_service,
        )

        chunk = PaperChunk(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            paper_id=UUID("00000000-0000-0000-0000-000000000002"),
            text="test text",
            page_number=1,
            chunk_index=0,
            char_start=0,
            char_end=9,
            char_count=9,
        )

        with patch.object(
            qdrant_service,
            "upsert_chunks",
            side_effect=RuntimeError("Qdrant upsert failed"),
        ):
            with pytest.raises(DocumentIndexingError, match="Qdrant upsert failed"):
                service.index_document(
                    paper_id=UUID("00000000-0000-0000-0000-000000000002"),
                    chunks=[chunk],
                )

    def test_index_document_returns_correct_count(
        self,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
    ) -> None:
        """Verify that index_document returns the number of indexed chunks."""
        service = DocumentIndexingService(
            embedding_service=embedding_service,
            qdrant_service=qdrant_service,
        )

        chunks = [
            PaperChunk(
                id=UUID(f"00000000-0000-0000-0000-{i:012d}"),
                paper_id=UUID("00000000-0000-0000-0000-000000000002"),
                text=f"This is chunk {i} with some text for embedding.",
                page_number=1,
                chunk_index=i,
                char_start=0,
                char_end=10,
                char_count=10,
            )
            for i in range(3)
        ]

        result = service.index_document(
            paper_id=UUID("00000000-0000-0000-0000-000000000002"),
            chunks=chunks,
        )
        assert result == 3
