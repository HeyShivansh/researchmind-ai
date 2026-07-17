"""
Paper service — business logic and transaction management for the
Paper domain aggregate.

The service layer is the sole owner of database transactions and
raises domain exceptions that are Framework-agnostic (no HTTP or
FastAPI dependency).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions.paper import DuplicatePaperError, PaperNotFoundError
from app.models.paper import Paper
from app.repositories.paper_repository import PaperRepository
from app.schemas.paper import PaperCreate


class PaperService:
    """
    Service for Paper business operations.

    Owns all transaction management (commit, rollback, refresh) and
    coordinates with the repository layer.  The repository is an
    internal implementation detail and is instantiated by the service.

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use for all database operations.

    Examples
    --------
    >>> service = PaperService(db_session)
    >>> paper = service.create_paper(PaperCreate(title="...", pdf_path="..."))
    """

    def __init__(self, session: Session) -> None:
        self._repository = PaperRepository(session)
        self._session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_paper(self, paper: PaperCreate) -> Paper:
        """
        Create a new paper.

        If the paper has a DOI, ensures no other paper with that DOI
        already exists before creating it.

        Parameters
        ----------
        paper : PaperCreate
            The validated creation data for the new paper.

        Returns
        -------
        Paper
            The newly created ORM instance, committed and refreshed.

        Raises
        ------
        DuplicatePaperError
            If another paper with the same DOI already exists.
        """
        if paper.doi is not None:
            existing = self._repository.get_by_doi(paper.doi)
            if existing is not None:
                raise DuplicatePaperError(paper.doi)

        instance = self._repository.create(**paper.model_dump())

        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        self._session.refresh(instance)
        return instance

    def get_paper(self, paper_id: UUID) -> Paper:
        """
        Retrieve a paper by its unique identifier.

        Parameters
        ----------
        paper_id : UUID
            The identifier of the paper to retrieve.

        Returns
        -------
        Paper
            The matching ORM instance.

        Raises
        ------
        PaperNotFoundError
            If no paper with ``paper_id`` exists.
        """
        paper = self._repository.get_by_id(paper_id)
        if paper is None:
            raise PaperNotFoundError(paper_id)
        return paper

    def list_papers(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Retrieve a paginated list of all papers.

        Parameters
        ----------
        skip : int
            Number of records to skip (OFFSET). Defaults to 0.
        limit : int
            Maximum number of records to return. Defaults to 100.

        Returns
        -------
        list[Paper]
            A list of Paper ORM instances.
        """
        return self._repository.list(skip=skip, limit=limit)
