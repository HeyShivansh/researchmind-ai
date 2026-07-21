"""
Paper repository — concrete repository for the Paper ORM model.

Provides domain-specific query methods on top of the generic CRUD
operations inherited from BaseRepository.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.paper import Paper
from app.repositories.base import BaseRepository


class PaperRepository(BaseRepository[Paper]):
    """
    Repository for ``Paper``-specific database queries.

    Inherits ``create``, ``get_by_id``, ``list``, ``exists``,
    ``count``, and ``delete`` from ``BaseRepository``.

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use for database operations.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, Paper)

    # ------------------------------------------------------------------
    # Paper-specific queries
    # ------------------------------------------------------------------

    def get_by_doi(self, doi: str) -> Paper | None:
        """
        Retrieve a paper by its Digital Object Identifier (DOI).

        Parameters
        ----------
        doi : str
            The DOI to search for.

        Returns
        -------
        Paper | None
            The matching paper, or ``None`` if no paper with that DOI exists.
        """
        stmt = self._stmt_select().where(Paper.doi == doi)
        return self._session.scalar(stmt)

    def search_by_title(self, query: str, *, limit: int = 20) -> list[Paper]:
        """
        Search for papers whose title contains the given query string.

        The search is case-insensitive and matches anywhere in the title.

        Parameters
        ----------
        query : str
            Search term to match against paper titles.
        limit : int
            Maximum number of results to return. Defaults to 20.

        Returns
        -------
        list[Paper]
            List of matching papers ordered by title ascending.
        """
        pattern = f"%{query}%"
        stmt = (
            self._stmt_select()
            .where(Paper.title.ilike(pattern))
            .order_by(Paper.title)
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def list_recent(self, *, limit: int = 20) -> list[Paper]:
        """
        Return the most recently added papers.

        Results are ordered by ``created_at`` descending.

        Parameters
        ----------
        limit : int
            Maximum number of papers to return. Defaults to 20.

        Returns
        -------
        list[Paper]
            List of the most recent papers.
        """
        stmt = (
            self._stmt_select()
            .order_by(Paper.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())
