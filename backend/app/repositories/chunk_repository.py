"""
Chunk repository — concrete repository for the PaperChunk ORM model.

Provides bulk-insert and paper-scoped query operations on top of the
generic CRUD operations inherited from BaseRepository.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.paper_chunk import PaperChunk
from app.repositories.base import BaseRepository


class ChunkRepository(BaseRepository[PaperChunk]):
    """
    Repository for ``PaperChunk``-specific database queries.

    Inherits ``create``, ``get_by_id``, ``list``, ``exists``,
    ``count``, and ``delete`` from ``BaseRepository``.

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use for database operations.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, PaperChunk)

    # ------------------------------------------------------------------
    # Chunk-specific queries
    # ------------------------------------------------------------------

    def create_many(self, chunks: list[PaperChunk]) -> list[PaperChunk]:
        """
        Add multiple chunk instances to the session at once.

        No commit is performed — transaction management is the
        responsibility of the caller.

        Parameters
        ----------
        chunks : list[PaperChunk]
            ORM instances to persist.

        Returns
        -------
        list[PaperChunk]
            The same instances, now tracked by the session.
        """
        for chunk in chunks:
            self._session.add(chunk)
        return chunks

    def list_by_paper(
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
            Number of chunks to skip (OFFSET). Defaults to 0.
        limit : int
            Maximum number of chunks to return. Defaults to 1000.

        Returns
        -------
        list[PaperChunk]
            Ordered list of chunks.
        """
        stmt = (
            self._stmt_select()
            .where(PaperChunk.paper_id == paper_id)
            .order_by(PaperChunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def count_for_paper(self, paper_id: UUID) -> int:
        """
        Count the number of chunks for a given paper.

        Parameters
        ----------
        paper_id : UUID
            The paper's unique identifier.

        Returns
        -------
        int
            Number of chunks.
        """
        stmt = (
            select(func.count())
            .select_from(PaperChunk)
            .where(PaperChunk.paper_id == paper_id)
        )
        result = self._session.execute(stmt).scalar()
        return int(result)  # type: ignore[arg-type]

    def get_by_ids(self, chunk_ids: list[UUID]) -> list[PaperChunk]:
        """
        Retrieve multiple chunks by their IDs in a single query.

        Parameters
        ----------
        chunk_ids : list[UUID]
            The unique identifiers of the chunks to retrieve.

        Returns
        -------
        list[PaperChunk]
            The matching ORM instances (order is not guaranteed — the
            caller should reorder to match the desired ranking).
        """
        if not chunk_ids:
            return []
        stmt = select(PaperChunk).where(PaperChunk.id.in_(chunk_ids))
        return list(self._session.scalars(stmt).all())

    def get_all_texts(self) -> list[tuple[UUID, str]]:
        """
        Retrieve all chunk IDs and their text content for BM25 indexing.

        Returns
        -------
        list[tuple[UUID, str]]
            ``(chunk_id, text)`` pairs for every chunk in the database.
        """
        stmt = select(PaperChunk.id, PaperChunk.text)
        rows = self._session.execute(stmt).all()
        return [(row.id, row.text) for row in rows]

    def delete_for_paper(self, paper_id: UUID) -> int:
        """
        Delete all chunks for a given paper.

        Parameters
        ----------
        paper_id : UUID
            The paper's unique identifier.

        Returns
        -------
        int
            Number of deleted rows.
        """
        stmt = select(PaperChunk).where(PaperChunk.paper_id == paper_id)
        chunks = list(self._session.scalars(stmt).all())
        for chunk in chunks:
            self._session.delete(chunk)
        return len(chunks)
