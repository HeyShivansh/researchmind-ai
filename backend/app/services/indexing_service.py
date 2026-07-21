"""
Document indexing service — orchestrates embedding generation and
vector store upsert for document chunks.

This service is the bridge between chunk persistence (PostgreSQL)
and the vector store (Qdrant).  It extracts text from persisted
chunks, embeds them in batch, and upserts into Qdrant in a single
operation.

The service is used by ``PaperService`` as part of the upload
pipeline, after chunks have been persisted to PostgreSQL.
"""

from __future__ import annotations

from uuid import UUID

from app.embeddings import EmbeddingService
from app.models.paper_chunk import PaperChunk
from app.vectorstore import QdrantService


class DocumentIndexingError(Exception):
    """Raised when document indexing (embedding or Qdrant upsert) fails."""


class DocumentIndexingService:
    """
    Service for indexing document chunks into the vector store.

    Coordinates embedding generation and Qdrant upsert as a single
    operation so that callers (e.g. ``PaperService``) can treat it
    as an atomic step in their pipeline.

    Parameters
    ----------
    embedding_service : EmbeddingService
        Service for generating embedding vectors from text.
    qdrant_service : QdrantService
        Service for upserting vectors into Qdrant.

    Examples
    --------
    >>> service = DocumentIndexingService(embedding_service, qdrant_service)
    >>> service.index_document(paper_id, chunks)
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
    ) -> None:
        self._embedding_service = embedding_service
        self._qdrant_service = qdrant_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_document(
        self,
        paper_id: UUID,
        chunks: list[PaperChunk],
    ) -> int:
        """
        Index all chunks for a document into the vector store.

        Extracts text from every chunk, generates embeddings in a
        single batch call, and upserts all vectors into Qdrant.

        Parameters
        ----------
        paper_id : UUID
            The paper's unique identifier (used in the Qdrant payload).
        chunks : list[PaperChunk]
            Persisted ORM chunk instances.  Each chunk must have
            ``id``, ``text``, ``page_number``, and ``chunk_index``
            populated.

        Returns
        -------
        int
            Number of vectors upserted into Qdrant.

        Raises
        ------
        DocumentIndexingError
            If embedding or Qdrant upsert fails.
        """
        if not chunks:
            return 0

        # -- Extract text from every chunk ------------------------------------
        chunk_texts = [chunk.text for chunk in chunks]

        # -- Generate embeddings in a single batch call -----------------------
        try:
            embeddings = self._embedding_service.embed_batch(chunk_texts)
        except Exception as exc:
            raise DocumentIndexingError(
                f"Failed to embed {len(chunks)} chunk(s) for "
                f"paper {paper_id}: {exc}"
            ) from exc

        # -- Build the (chunk_id, vector, paper_id, page_number, chunk_index) tuples
        points = [
            (
                chunk.id,
                emb.vector,
                paper_id,
                chunk.page_number,
                chunk.chunk_index,
            )
            for chunk, emb in zip(chunks, embeddings, strict=True)
        ]

        # -- Upsert everything into Qdrant in a single batch ------------------
        try:
            self._qdrant_service.upsert_chunks(points)
        except Exception as exc:
            raise DocumentIndexingError(
                f"Failed to upsert {len(points)} vector(s) into "
                f"Qdrant for paper {paper_id}: {exc}"
            ) from exc

        return len(points)
