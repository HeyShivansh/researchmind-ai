"""
Chunk persistence service — coordinates chunk storage for the
ResearchMind AI platform.

This service is the sole bridge between the chunking subsystem (which
produces ``DocumentChunk`` dataclasses) and the database (which stores
``PaperChunk`` ORM instances).  No SQLAlchemy models are exposed to
callers of this service.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.chunking.models import DocumentChunk
from app.models.paper_chunk import PaperChunk
from app.repositories.chunk_repository import ChunkRepository


class ChunkPersistenceService:
    """
    Service for persisting and retrieving document chunks.

    Converts between the chunking subsystem's ``DocumentChunk``
    dataclasses and the database ``PaperChunk`` ORM model.  All
    transaction management is exposed to the caller (commit/rollback
    happens at a higher level, typically in the upload pipeline).

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use for all database operations.

    Examples
    --------
    >>> service = ChunkPersistenceService(db_session)
    >>> chunks = [DocumentChunk(...), DocumentChunk(...)]
    >>> service.persist_chunks(paper_id=paper.id, chunks=chunks)
    """

    def __init__(self, session: Session) -> None:
        self._repository = ChunkRepository(session)
        self._session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def persist_chunks(
        self,
        paper_id: UUID,
        chunks: list[DocumentChunk],
    ) -> list[PaperChunk]:
        """
        Convert ``DocumentChunk`` dataclasses to ``PaperChunk`` ORM
        instances and add them to the session.

        Parameters
        ----------
        paper_id : UUID
            The parent paper's identifier.
        chunks : list[DocumentChunk]
            Chunks produced by the chunking subsystem.

        Returns
        -------
        list[PaperChunk]
            The newly created ORM instances, tracked by the session
            but **not yet committed**.
        """
        orm_chunks = self._document_chunks_to_orm(paper_id, chunks)
        return self._repository.create_many(orm_chunks)

    def list_chunks(
        self,
        paper_id: UUID,
        *,
        skip: int = 0,
        limit: int = 1000,
    ) -> list[PaperChunk]:
        """
        Retrieve chunks for a paper, ordered by chunk index.

        Parameters
        ----------
        paper_id : UUID
            The paper's unique identifier.
        skip : int
            Number of chunks to skip. Defaults to 0.
        limit : int
            Maximum number of chunks to return. Defaults to 1000.

        Returns
        -------
        list[PaperChunk]
            Ordered list of ORM instances.
        """
        return self._repository.list_by_paper(paper_id, skip=skip, limit=limit)

    def count_chunks(self, paper_id: UUID) -> int:
        """
        Count the total number of chunks for a paper.

        Parameters
        ----------
        paper_id : UUID
            The paper's unique identifier.

        Returns
        -------
        int
            Number of chunks.
        """
        return self._repository.count_for_paper(paper_id)

    def delete_chunks(self, paper_id: UUID) -> int:
        """
        Delete all chunks for a paper.

        Parameters
        ----------
        paper_id : UUID
            The paper's unique identifier.

        Returns
        -------
        int
            Number of deleted rows.
        """
        return self._repository.delete_for_paper(paper_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _document_chunks_to_orm(
        paper_id: UUID,
        chunks: list[DocumentChunk],
    ) -> list[PaperChunk]:
        """
        Convert a list of ``DocumentChunk`` dataclasses into a list of
        ``PaperChunk`` ORM instances.

        The chunk's UUID ``id`` is preserved so that the downstream
        metadata remains traceable.

        Parameters
        ----------
        paper_id : UUID
            The parent paper's identifier.
        chunks : list[DocumentChunk]
            Chunks produced by the chunking subsystem.

        Returns
        -------
        list[PaperChunk]
            ORM instances (not yet added to a session).
        """
        return [
            PaperChunk(
                id=chunk.id,
                paper_id=paper_id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                char_count=chunk.char_count,
            )
            for chunk in chunks
        ]
