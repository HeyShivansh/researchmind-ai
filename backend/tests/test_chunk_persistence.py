"""
Integration tests for chunk persistence.

Tests the full round-trip: creating a Paper, processing and chunking
its PDF, persisting the chunks via ChunkPersistenceService, and
verifying the data layer behaves correctly under various scenarios.

These tests use real PDF files generated during test execution.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import fitz
import pytest
from sqlalchemy.orm import Session

from app.chunking import DocumentChunk, RecursiveCharacterChunker
from app.models.paper import Paper
from app.models.paper_chunk import PaperChunk
from app.processing import DocumentProcessor
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.paper_repository import PaperRepository
from app.services.chunk_persistence_service import ChunkPersistenceService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf(path: Path, text: str = "Hello, world!") -> Path:
    """Create a simple single-page PDF at *path* and return the path."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def _make_multi_page_pdf(path: Path, page_count: int = 3) -> Path:
    """Create a multi-page PDF with one line of text per page."""
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text(
            fitz.Point(72, 72), f"Page {i + 1} content", fontsize=12
        )
    doc.save(str(path))
    doc.close()
    return path


def _make_text_heavy_pdf(path: Path, text: str) -> Path:
    """
    Create a single-page PDF with long text content.

    The text is inserted in multiple runs to fill the page so that
    the chunker produces multiple chunks.
    """
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), text, fontsize=11)
    doc.save(str(path))
    doc.close()
    return path


def _create_paper(db_session: Session, title: str = "Test Paper") -> Paper:
    """Create and commit a minimal Paper record, return it."""
    repo = PaperRepository(db_session)
    paper = repo.create(
        title=title,
        pdf_path="test/path.pdf",
    )
    db_session.commit()
    db_session.refresh(paper)
    return paper


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def chunk_repository(db_session: Session) -> ChunkRepository:
    """Provide a ChunkRepository wired to the test database session."""
    return ChunkRepository(db_session)


@pytest.fixture()
def persistence_service(
    db_session: Session,
) -> ChunkPersistenceService:
    """Provide a ChunkPersistenceService wired to the test session."""
    return ChunkPersistenceService(db_session)


@pytest.fixture()
def chunker() -> RecursiveCharacterChunker:
    """Provide a chunker with small size for deterministic testing."""
    return RecursiveCharacterChunker(chunk_size=100, chunk_overlap=10)


@pytest.fixture()
def processor() -> DocumentProcessor:
    """Provide a fresh DocumentProcessor instance."""
    return DocumentProcessor()


@pytest.fixture()
def paper(db_session: Session) -> Paper:
    """Create and return a committed Paper for use in chunk tests."""
    return _create_paper(db_session, "Chunk Test Paper")


# ---------------------------------------------------------------------------
# Persist chunks
# ---------------------------------------------------------------------------


class TestPersistChunks:
    """Tests for persisting DocumentChunk objects."""

    def test_persist_single_chunk(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
    ) -> None:
        """Verify a single chunk can be persisted."""
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=0,
                text="Hello, world!",
                char_start=0,
                char_end=13,
                char_count=13,
            )
        ]
        result = persistence_service.persist_chunks(paper.id, chunks)
        assert len(result) == 1
        assert result[0].paper_id == paper.id
        assert result[0].text == "Hello, world!"

    def test_persist_multiple_chunks(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
    ) -> None:
        """Verify multiple chunks are persisted with correct ordering."""
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=0,
                text="First chunk",
                char_start=0,
                char_end=11,
                char_count=11,
            ),
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000002"),
                page_number=1,
                chunk_index=1,
                text="Second chunk",
                char_start=11,
                char_end=23,
                char_count=12,
            ),
        ]
        result = persistence_service.persist_chunks(paper.id, chunks)
        assert len(result) == 2
        assert result[0].chunk_index == 0
        assert result[1].chunk_index == 1

    def test_chunk_id_preserved(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify the chunk UUID survives the round-trip."""
        chunk_id = UUID("11111111-1111-1111-1111-111111111111")
        chunks = [
            DocumentChunk(
                id=chunk_id,
                page_number=1,
                chunk_index=0,
                text="Preserved ID",
                char_start=0,
                char_end=12,
                char_count=12,
            )
        ]
        persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        # Read back directly from the DB.
        retrieved = db_session.get(PaperChunk, chunk_id)
        assert retrieved is not None
        assert retrieved.id == chunk_id
        assert retrieved.text == "Preserved ID"


# ---------------------------------------------------------------------------
# Retrieve ordered chunks
# ---------------------------------------------------------------------------


class TestRetrieveOrderedChunks:
    """Tests for retrieving chunks in order."""

    def test_list_by_paper_ordered(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify chunks are returned in chunk_index order."""
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=2,
                text="Third",
                char_start=10,
                char_end=15,
                char_count=5,
            ),
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000002"),
                page_number=1,
                chunk_index=0,
                text="First",
                char_start=0,
                char_end=5,
                char_count=5,
            ),
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000003"),
                page_number=1,
                chunk_index=1,
                text="Second",
                char_start=5,
                char_end=10,
                char_count=5,
            ),
        ]
        persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        retrieved = persistence_service.list_chunks(paper.id)
        assert len(retrieved) == 3
        assert retrieved[0].text == "First"
        assert retrieved[1].text == "Second"
        assert retrieved[2].text == "Third"

    def test_list_by_paper_empty(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
    ) -> None:
        """Verify a paper with no chunks returns an empty list."""
        retrieved = persistence_service.list_chunks(paper.id)
        assert retrieved == []

    def test_list_by_paper_pagination(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify skip and limit work correctly."""
        chunks = [
            DocumentChunk(
                id=UUID(f"00000000-0000-0000-0000-000000000{str(i).zfill(3)}"),
                page_number=1,
                chunk_index=i,
                text=f"Chunk {i}",
                char_start=i * 10,
                char_end=i * 10 + 5,
                char_count=5,
            )
            for i in range(10)
        ]
        persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        # Get middle 3 entries.
        retrieved = persistence_service.list_chunks(paper.id, skip=3, limit=3)
        assert len(retrieved) == 3
        assert retrieved[0].text == "Chunk 3"
        assert retrieved[1].text == "Chunk 4"
        assert retrieved[2].text == "Chunk 5"


# ---------------------------------------------------------------------------
# Chunk metadata preserved
# ---------------------------------------------------------------------------


class TestChunkMetadataPreserved:
    """Tests that all chunk metadata fields survive the round-trip."""

    def test_all_fields_preserved(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify every field on DocumentChunk is stored and retrieved correctly."""
        chunk = DocumentChunk(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            page_number=3,
            chunk_index=7,
            text="Specific metadata content",
            char_start=100,
            char_end=125,
            char_count=25,
        )
        persistence_service.persist_chunks(paper.id, [chunk])
        db_session.commit()

        retrieved = persistence_service.list_chunks(paper.id)
        assert len(retrieved) == 1
        orm = retrieved[0]
        assert orm.id == chunk.id
        assert orm.paper_id == paper.id
        assert orm.page_number == 3
        assert orm.chunk_index == 7
        assert orm.text == "Specific metadata content"
        assert orm.char_start == 100
        assert orm.char_end == 125
        assert orm.char_count == 25
        assert orm.created_at is not None


# ---------------------------------------------------------------------------
# Count chunks
# ---------------------------------------------------------------------------


class TestCountChunks:
    """Tests for counting chunks per paper."""

    def test_count_zero_chunks(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
    ) -> None:
        """Verify a paper with no chunks returns a count of 0."""
        assert persistence_service.count_chunks(paper.id) == 0

    def test_count_matches_inserted(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify count equals the number of inserted chunks."""
        chunks = [
            DocumentChunk(
                id=UUID(f"00000000-0000-0000-0000-000000000{str(i).zfill(3)}"),
                page_number=1,
                chunk_index=i,
                text=f"Chunk {i}",
                char_start=i * 10,
                char_end=i * 10 + 5,
                char_count=5,
            )
            for i in range(5)
        ]
        persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()
        assert persistence_service.count_chunks(paper.id) == 5


# ---------------------------------------------------------------------------
# Delete paper cascades
# ---------------------------------------------------------------------------


class TestDeletePaperCascade:
    """Tests that deleting a Paper also removes its chunks."""

    def test_delete_cascade_removes_chunks(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        chunk_repository: ChunkRepository,
        db_session: Session,
    ) -> None:
        """Verify chunks are removed when the parent Paper is deleted."""
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=0,
                text="Cascade test",
                char_start=0,
                char_end=11,
                char_count=11,
            )
        ]
        persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        assert chunk_repository.count_for_paper(paper.id) == 1

        # Delete the paper.
        paper_repo = PaperRepository(db_session)
        paper_repo.delete(paper.id)
        db_session.commit()

        assert chunk_repository.count_for_paper(paper.id) == 0

    def test_delete_orphan_chunks(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        chunk_repository: ChunkRepository,
        db_session: Session,
    ) -> None:
        """Verify delete-orphan removes chunks when Paper is deleted via cascade."""
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=0,
                text="Orphan test",
                char_start=0,
                char_end=10,
                char_count=10,
            )
        ]
        persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        # Delete paper directly from DB to test ondelete cascade.
        db_session.delete(paper)
        db_session.commit()

        # Chunks should be gone.
        remaining = chunk_repository.list_by_paper(paper.id)
        assert remaining == []


# ---------------------------------------------------------------------------
# Rollback removes chunks
# ---------------------------------------------------------------------------


class TestRollbackRemovesChunks:
    """Tests that a session rollback removes pending chunk records."""

    def test_rollback_clears_chunks(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify chunks added to the session vanish after rollback."""
        paper_id = paper.id
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=0,
                text="Rollback me",
                char_start=0,
                char_end=10,
                char_count=10,
            )
        ]
        persistence_service.persist_chunks(paper_id, chunks)

        # Verify chunks exist in the session before rollback.
        repo = ChunkRepository(db_session)
        assert repo.count_for_paper(paper_id) == 1

        # Roll back instead of commit.
        db_session.rollback()

        # After rollback, no chunks should exist.
        assert repo.count_for_paper(paper_id) == 0

    def test_chunks_not_persisted_without_commit(
        self,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
        test_engine,
    ) -> None:
        """Verify chunks are not persisted to the database before commit.

        Uses a separate SQLAlchemy engine connection to verify that
        uncommitted chunks are not visible outside the test transaction.
        """
        from sqlalchemy import create_engine

        paper_id = paper.id
        chunks = [
            DocumentChunk(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                page_number=1,
                chunk_index=0,
                text="No commit",
                char_start=0,
                char_end=8,
                char_count=8,
            )
        ]
        persistence_service.persist_chunks(paper_id, chunks)

        # No commit — use a separate connection to verify nothing is visible.
        from sqlalchemy import text as sa_text
        from app.database.base import Base

        other_conn = test_engine.connect()
        try:
            count = other_conn.execute(
                sa_text(
                    "SELECT COUNT(*) FROM paper_chunks WHERE paper_id = :pid"
                ),
                {"pid": paper_id},
            ).scalar()
            assert count == 0
        finally:
            other_conn.close()

        # Within the test transaction, the chunks ARE visible (read uncommitted
        # is not possible but PostgreSQL's MVCC means the same transaction sees
        # its own uncommitted changes). Verify that for completeness.
        assert (
            ChunkRepository(db_session).count_for_paper(paper_id) == 1
        )


# ---------------------------------------------------------------------------
# Multiple papers isolated
# ---------------------------------------------------------------------------


class TestMultiplePapersIsolated:
    """Tests that chunks for different papers are properly isolated."""

    def test_chunks_not_shared_across_papers(
        self,
        persistence_service: ChunkPersistenceService,
        db_session: Session,
    ) -> None:
        """Verify a chunk is only retrievable via its own paper."""
        paper_a = _create_paper(db_session, "Paper A")
        paper_b = _create_paper(db_session, "Paper B")

        persistence_service.persist_chunks(
            paper_a.id,
            [
                DocumentChunk(
                    id=UUID("00000000-0000-0000-0000-000000000001"),
                    page_number=1,
                    chunk_index=0,
                    text="Only in A",
                    char_start=0,
                    char_end=8,
                    char_count=8,
                )
            ],
        )
        persistence_service.persist_chunks(
            paper_b.id,
            [
                DocumentChunk(
                    id=UUID("00000000-0000-0000-0000-000000000002"),
                    page_number=1,
                    chunk_index=0,
                    text="Only in B",
                    char_start=0,
                    char_end=8,
                    char_count=8,
                )
            ],
        )
        db_session.commit()

        # Paper A should only have its own chunk.
        chunks_a = persistence_service.list_chunks(paper_a.id)
        assert len(chunks_a) == 1
        assert chunks_a[0].text == "Only in A"

        # Paper B should only have its own chunk.
        chunks_b = persistence_service.list_chunks(paper_b.id)
        assert len(chunks_b) == 1
        assert chunks_b[0].text == "Only in B"

    def test_multiple_papers_have_independent_counts(
        self,
        persistence_service: ChunkPersistenceService,
        db_session: Session,
    ) -> None:
        """Verify chunk counts are per-paper and independent."""
        paper_a = _create_paper(db_session, "Paper A")
        paper_b = _create_paper(db_session, "Paper B")

        # Paper A gets 3 chunks.
        persistence_service.persist_chunks(
            paper_a.id,
            [
                DocumentChunk(
                    id=UUID(f"00000000-0000-0000-0000-00000000000{i}"),
                    page_number=1,
                    chunk_index=i,
                    text=f"A-{i}",
                    char_start=i * 10,
                    char_end=i * 10 + 5,
                    char_count=5,
                )
                for i in range(3)
            ],
        )
        # Paper B gets 2 chunks.
        persistence_service.persist_chunks(
            paper_b.id,
            [
                DocumentChunk(
                    id=UUID(f"00000000-0000-0000-0000-00000000001{i}"),
                    page_number=1,
                    chunk_index=i,
                    text=f"B-{i}",
                    char_start=i * 10,
                    char_end=i * 10 + 5,
                    char_count=5,
                )
                for i in range(2)
            ],
        )
        db_session.commit()

        assert persistence_service.count_chunks(paper_a.id) == 3
        assert persistence_service.count_chunks(paper_b.id) == 2


# ---------------------------------------------------------------------------
# Full pipeline: process, chunk, persist
# ---------------------------------------------------------------------------


class TestFullPipeline:
    """Tests that exercise the full process → chunk → persist flow."""

    def test_single_page_pipeline(
        self,
        tmp_path: Path,
        processor: DocumentProcessor,
        chunker: RecursiveCharacterChunker,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify a single-page PDF flows through processing, chunking, and persistence."""
        text = (
            "This is a test document with enough text to generate "
            "multiple chunks when using the small chunk size configured "
            "in the test fixture. The quick brown fox jumps over the lazy dog."
        )
        pdf = _make_text_heavy_pdf(tmp_path / "pipeline.pdf", text)

        # Process
        processed = processor.process(pdf)
        assert len(processed.pages) == 1

        # Chunk
        chunks = chunker.chunk(processed)
        assert len(chunks) >= 1

        # Persist
        persisted = persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        assert len(persisted) == len(chunks)
        assert persistence_service.count_chunks(paper.id) == len(chunks)

        # Verify round-trip metadata
        retrieved = persistence_service.list_chunks(paper.id)
        for i, (original, orm) in enumerate(zip(chunks, retrieved)):
            assert orm.page_number == original.page_number
            assert orm.chunk_index == original.chunk_index
            assert orm.text == original.text
            assert orm.char_start == original.char_start
            assert orm.char_end == original.char_end
            assert orm.char_count == original.char_count

    def test_multi_page_pipeline(
        self,
        tmp_path: Path,
        processor: DocumentProcessor,
        chunker: RecursiveCharacterChunker,
        persistence_service: ChunkPersistenceService,
        paper: Paper,
        db_session: Session,
    ) -> None:
        """Verify a multi-page PDF generates chunks per page correctly."""
        pdf = _make_multi_page_pdf(tmp_path / "multi-pipeline.pdf", page_count=3)

        processed = processor.process(pdf)
        assert len(processed.pages) == 3

        chunks = chunker.chunk(processed)
        assert len(chunks) >= 3  # At least one chunk per page.

        persisted = persistence_service.persist_chunks(paper.id, chunks)
        db_session.commit()

        assert len(persisted) == len(chunks)

        # Verify page numbers are preserved.
        page_numbers = {orm.page_number for orm in persisted}
        assert page_numbers == {1, 2, 3}

        # Verify ordering by chunk_index.
        retrieved = persistence_service.list_chunks(paper.id)
        for i in range(1, len(retrieved)):
            assert retrieved[i].chunk_index > retrieved[i - 1].chunk_index
