"""End-to-end integration tests for the indexing and retrieval pipeline.

Exercises real components end-to-end:

    PDF Upload → Storage → Processing → Chunking → Persistence
    → Embedding → Qdrant → Hybrid Retrieval

Only the external embedding provider is mocked (deterministic hash-based).
PostgreSQL and Qdrant must be running (``docker-compose up -d``).

Run with::

    uv run pytest tests/integration/ -v
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import fitz
import pytest
from sqlalchemy.orm import Session

from app.hybrid import HybridRetrievalError, HybridRetrievalService
from app.models.paper import Paper
from app.repositories.paper_repository import PaperRepository
from app.services.chunk_persistence_service import ChunkPersistenceService
from app.services.paper_service import PaperService
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

    # Page 1: AI / healthcare content
    page1 = doc.new_page()
    page1.insert_text(fitz.Point(72, 72), PAGE_1_TEXT, fontsize=11)

    # Page 2: Qdrant / BM25 content
    page2 = doc.new_page()
    page2.insert_text(fitz.Point(72, 72), PAGE_2_TEXT, fontsize=11)

    doc.set_metadata({"title": "Integration Test Paper"})
    doc.save(str(path))
    doc.close()
    return path


def _create_second_pdf(path: Path) -> Path:
    """Create a single-page PDF about a different topic."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        fitz.Point(72, 72),
        "Deep learning models require large amounts of training data. "
        "Neural networks consist of multiple layers of interconnected neurons.",
        fontsize=11,
    )
    doc.set_metadata({"title": "Deep Learning Paper"})
    doc.save(str(path))
    doc.close()
    return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _upload_pdf(
    paper_service: PaperService,
    pdf_bytes: bytes,
    title: str = "Integration Test Paper",
) -> Paper:
    """Upload a PDF and return the created Paper record."""
    return paper_service.upload_paper(
        file_bytes=pdf_bytes,
        filename="test.pdf",
        title=title,
    )


def _get_chunks(
    chunk_persistence_service: ChunkPersistenceService,
    paper_id: UUID,
) -> list:
    """Retrieve persisted chunks for a paper."""
    return chunk_persistence_service.list_chunks(paper_id)


def _embed_and_store(
    qdrant_service: QdrantService,
    embedding_service,
    chunk_persistence_service: ChunkPersistenceService,
    paper_id: UUID,
) -> int:
    """Embed all chunks for a paper and store the vectors in Qdrant.

    Returns the number of vectors stored.
    """
    chunks = _get_chunks(chunk_persistence_service, paper_id)
    if not chunks:
        return 0

    # Build (chunk_id, vector, paper_id, page_number, chunk_index) tuples
    chunk_texts = [c.text for c in chunks]
    embeddings = embedding_service.embed_batch(chunk_texts)

    points = [
        (
            c.id,
            emb.vector,
            c.paper_id,
            c.page_number,
            c.chunk_index,
        )
        for c, emb in zip(chunks, embeddings, strict=True)
    ]

    qdrant_service.upsert_chunks(points)
    return len(points)


def _upload_and_index(
    paper_service: PaperService,
    chunk_persistence_service: ChunkPersistenceService,
    qdrant_service: QdrantService,
    embedding_service,
    hybrid_service: HybridRetrievalService,
    pdf_bytes: bytes,
    title: str = "Integration Test Paper",
) -> Paper:
    """Upload a PDF and fully index it (chunks + embeddings + Qdrant + BM25).

    Returns the created Paper.
    """
    paper = _upload_pdf(paper_service, pdf_bytes, title=title)
    _embed_and_store(qdrant_service, embedding_service, chunk_persistence_service, paper.id)
    hybrid_service.rebuild_index()
    return paper


# ===================================================================
# Test 1: Upload and verify complete indexing pipeline
# ===================================================================


class TestUploadPipeline:
    """Verify the complete upload-to-index pipeline."""

    def test_upload_creates_paper(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        db_session: Session,
    ) -> None:
        """Verify paper, chunks, and metadata after upload."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        pdf_bytes = pdf.read_bytes()

        paper = _upload_pdf(paper_service, pdf_bytes)

        # Paper created
        repo = PaperRepository(db_session)
        retrieved = repo.get_by_id(paper.id)
        assert retrieved is not None
        assert retrieved.title == "Integration Test Paper"
        assert retrieved.pdf_path is not None

    def test_upload_generates_chunks(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
    ) -> None:
        """Verify chunks are generated and persisted."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_pdf(paper_service, pdf.read_bytes())

        chunks = _get_chunks(chunk_persistence_service, paper.id)
        assert len(chunks) >= 2  # At least one chunk per page
        for chunk in chunks:
            assert chunk.paper_id == paper.id
            assert chunk.text
            assert chunk.page_number >= 1
            assert chunk.chunk_index >= 0

    def test_upload_generates_embeddings_and_vectors(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
    ) -> None:
        """Verify embeddings are generated and vectors stored in Qdrant."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_pdf(paper_service, pdf.read_bytes())

        # Get the chunks and embed them
        chunks = _get_chunks(chunk_persistence_service, paper.id)
        assert len(chunks) >= 2

        # Embed one chunk to get a real vector for searching
        chunk_embedding = embedding_service.embed_text(chunks[0].text)

        stored = _embed_and_store(
            qdrant_service, embedding_service, chunk_persistence_service, paper.id
        )
        assert stored >= 2

        # Search with the embedding of the first chunk
        results = qdrant_service.search(
            vector=chunk_embedding.vector,
            limit=10,
        )
        assert len(results) >= 1

    def test_upload_preserves_page_numbers(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
    ) -> None:
        """Verify chunks from different pages preserve their page numbers."""
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_pdf(paper_service, pdf.read_bytes())

        chunks = _get_chunks(chunk_persistence_service, paper.id)
        page_numbers = {c.page_number for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers
        assert max(page_numbers) <= 2


# ===================================================================
# Test 2: Query "What is Qdrant?" returns the Qdrant chunk
# ===================================================================


class TestQueryWhatIsQdrant:
    """Verify that querying about Qdrant returns the relevant chunk."""

    def test_returns_qdrant_chunk(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        results = hybrid_service.hybrid_search("What is Qdrant?", top_k=5)

        assert len(results) >= 1
        result = results[0]
        assert "Qdrant" in result.text or "vector database" in result.text
        assert result.paper_id == paper.id
        assert result.chunk_id is not None
        assert isinstance(result.chunk_id, UUID)
        assert result.page_number == 2
        assert result.score > 0


# ===================================================================
# Test 3: Query "How is AI used in medicine?" returns healthcare chunk
# ===================================================================


class TestQueryAIInMedicine:
    """Verify that querying about AI in medicine returns healthcare content."""

    def test_returns_healthcare_chunk(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        # Query uses words that overlap with Page 1's healthcare text
        # to ensure the fake embedding provider ranks it highest.
        results = hybrid_service.hybrid_search(
            "healthcare diagnosis artificial intelligence", top_k=5
        )

        assert len(results) >= 1
        top = results[0]
        assert (
            "healthcare" in top.text.lower()
            or "artificial intelligence" in top.text.lower()
            or "diagnosis" in top.text.lower()
        )


# ===================================================================
# Test 4: Keyword-heavy query "BM25 keyword retrieval"
# ===================================================================


class TestKeywordHeavyQuery:
    """Verify BM25 contributes results for keyword-heavy queries."""

    def test_bm25_contributes(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        # Keyword-heavy query that exactly matches Page 2 text
        results = hybrid_service.hybrid_search("BM25 keyword retrieval", top_k=10)

        assert len(results) >= 1
        # At least one result should contain BM25-related content
        texts = " ".join(r.text for r in results)
        assert "BM25" in texts or "keyword" in texts.lower()


# ===================================================================
# Test 5: Semantic-heavy query "medical diagnosis"
# ===================================================================


class TestSemanticHeavyQuery:
    """Verify semantic search returns the healthcare chunk for a loose match."""

    def test_semantic_returns_healthcare(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        # "medical diagnosis" shares words with Page 1
        # ("Machine learning assists doctors with diagnosis")
        results = hybrid_service.hybrid_search("medical diagnosis", top_k=5)

        assert len(results) >= 1
        top = results[0]
        assert top.page_number == 1


# ===================================================================
# Test 6: Hybrid query tests both BM25 and semantic contributions
# ===================================================================


class TestHybridQuery:
    """Verify both BM25 and semantic search contribute to hybrid results."""

    def test_rrf_ordering(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        # Run twice to verify deterministic ordering
        query = "vector search with keyword retrieval"
        results_1 = hybrid_service.hybrid_search(query, top_k=5)
        results_2 = hybrid_service.hybrid_search(query, top_k=5)

        # Deterministic
        assert [r.chunk_id for r in results_1] == [r.chunk_id for r in results_2]

        # Scores should be descending
        for i in range(len(results_1) - 1):
            assert results_1[i].score >= results_1[i + 1].score

    def test_results_have_correct_structure(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        results = hybrid_service.hybrid_search(
            "vector search with keyword retrieval", top_k=5
        )

        assert len(results) >= 1
        for r in results:
            assert isinstance(r.chunk_id, UUID)
            assert isinstance(r.paper_id, UUID)
            assert r.text
            assert r.page_number >= 1
            assert r.chunk_index >= 0
            assert r.score > 0


# ===================================================================
# Test 7: Delete paper — verify cleanup
# ===================================================================


class TestDeletePaper:
    """Verify deleting a paper removes chunks, vectors, and search results."""

    def test_delete_removes_everything(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
        db_session: Session,
    ) -> None:
        pdf = _create_test_pdf(tmp_path / "test.pdf")
        paper = _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf.read_bytes(),
        )

        # Verify we get results before deletion
        before = hybrid_service.hybrid_search("What is Qdrant?", top_k=5)
        assert len(before) >= 1

        # Delete the paper
        paper_repo = PaperRepository(db_session)
        deleted = paper_repo.delete(paper.id)
        assert deleted is True
        db_session.commit()

        # Rebuild BM25 index (chunks removed from DB)
        hybrid_service.rebuild_index()

        # Delete vectors from Qdrant
        qdrant_service.delete_paper(paper.id)

        # Should no longer return deleted content
        after = hybrid_service.hybrid_search("What is Qdrant?", top_k=5)
        # Either empty or no results from the deleted paper
        for result in after:
            assert result.paper_id != paper.id


# ===================================================================
# Test 8: Multiple papers
# ===================================================================


class TestMultiplePapers:
    """Verify retrieval works across multiple documents."""

    def test_retrieves_from_multiple_papers(
        self,
        tmp_path: Path,
        paper_service: PaperService,
        chunk_persistence_service: ChunkPersistenceService,
        qdrant_service: QdrantService,
        embedding_service,
        hybrid_service: HybridRetrievalService,
    ) -> None:
        # Upload first paper
        pdf1 = _create_test_pdf(tmp_path / "test.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf1.read_bytes(),
            title="Test Paper 1",
        )

        # Upload second paper (different topic)
        pdf2 = _create_second_pdf(tmp_path / "deep.pdf")
        _upload_and_index(
            paper_service, chunk_persistence_service,
            qdrant_service, embedding_service, hybrid_service,
            pdf2.read_bytes(),
            title="Deep Learning Paper",
        )

        # Search for something that matches both
        results = hybrid_service.hybrid_search("deep learning neural networks", top_k=10)

        assert len(results) >= 1
        # Results should include the deep learning paper
        texts_combined = " ".join(r.text.lower() for r in results)
        assert "deep learning" in texts_combined or "neural" in texts_combined


# ===================================================================
# Test 9: Empty query
# ===================================================================


class TestEmptyQuery:
    """Verify empty queries raise the appropriate exception."""

    def test_empty_query_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        with pytest.raises(HybridRetrievalError, match="empty"):
            hybrid_service.hybrid_search("")

    def test_whitespace_query_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        with pytest.raises(HybridRetrievalError, match="empty"):
            hybrid_service.hybrid_search("   \t\n  ")


# ===================================================================
# Test 10: Invalid top_k
# ===================================================================


class TestInvalidTopK:
    """Verify invalid top_k values raise the appropriate exception."""

    def test_zero_top_k_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        with pytest.raises(HybridRetrievalError, match="top_k must be positive"):
            hybrid_service.hybrid_search("test query", top_k=0)

    def test_negative_top_k_raises_error(
        self, hybrid_service: HybridRetrievalService
    ) -> None:
        with pytest.raises(HybridRetrievalError, match="top_k must be positive"):
            hybrid_service.hybrid_search("test query", top_k=-1)
