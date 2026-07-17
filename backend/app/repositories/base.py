"""
Base repository providing generic CRUD operations for SQLAlchemy ORM models.

Follows the repository pattern:
- No business logic.
- No transaction management (commit/rollback).
- No FastAPI dependencies.
- Operates solely on the database session and ORM model.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base

# ---------------------------------------------------------------------------
# Generic type variable bound to the SQLAlchemy declarative base.
# Concrete repositories will bind this to their specific model class.
# ---------------------------------------------------------------------------
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository with standard CRUD operations for a SQLAlchemy ORM model.

    All methods operate on the provided session without committing or
    rolling back — transaction management is the responsibility of the
    caller (service layer or higher).

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use for database operations.
    model_class : type[ModelT]
        The ORM model class this repository manages.

    Examples
    --------
    >>> repo = BaseRepository(db_session, Paper)
    >>> paper = repo.create(title="My Paper", pdf_path="/tmp/paper.pdf")
    >>> found = repo.get_by_id(paper.id)
    """

    def __init__(self, session: Session, model_class: type[ModelT]) -> None:
        if not issubclass(model_class, Base):
            raise TypeError(
                f"model_class must be a subclass of Base, got {model_class}"
            )
        self._session = session
        self._model_class = model_class

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _stmt_select(self) -> select:
        """Return a base ``select`` statement for the managed model."""
        return select(self._model_class)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, **kwargs: object) -> ModelT:
        """
        Build a new model instance and add it to the session.

        Parameters
        ----------
        **kwargs : object
            Column values for the new record.

        Returns
        -------
        ModelT
            The newly created ORM instance (not yet flushed/committed).

        Raises
        ------
        TypeError
            If any ``kwargs`` value is incompatible with the model column.
        """
        instance = self._model_class(**kwargs)
        self._session.add(instance)
        return instance

    def get_by_id(self, record_id: object) -> ModelT | None:
        """
        Retrieve a record by its primary key.

        Parameters
        ----------
        record_id : object
            Primary key value of the record to fetch.

        Returns
        -------
        ModelT | None
            The matching ORM instance, or ``None`` if no record exists.
        """
        return self._session.get(self._model_class, record_id)

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelT]:
        """
        Retrieve a paginated list of all records.

        No ordering is applied by default — the row order is
        determined by the database engine.  Concrete repositories
        may add ordering when needed.

        Parameters
        ----------
        skip : int
            Number of records to skip (OFFSET). Defaults to 0.
        limit : int
            Maximum number of records to return. Defaults to 100.

        Returns
        -------
        list[ModelT]
            A list of ORM instances.
        """
        stmt = self._stmt_select().offset(skip).limit(limit)
        return list(self._session.scalars(stmt).all())

    def exists(self, **filters: object) -> bool:
        """
        Check whether at least one record matching the given filters exists.

        Parameters
        ----------
        **filters : object
            Column-value pairs for the WHERE clause.

        Returns
        -------
        bool
            ``True`` if a matching record exists, ``False`` otherwise.

        Examples
        --------
        >>> repo.exists(doi="10.1234/example")
        True
        """
        stmt = select(
            select(self._model_class)
            .filter_by(**filters)
            .exists()
        )
        result = self._session.execute(stmt).scalar()
        return bool(result)

    def count(self) -> int:
        """
        Return the total number of records in the table.

        Returns
        -------
        int
            Record count.
        """
        stmt = select(func.count()).select_from(self._model_class)
        result = self._session.execute(stmt).scalar()
        # ``func.count()`` always returns a non-None int, so the cast is safe.
        return int(result)  # type: ignore[arg-type]

    def delete(self, record_id: object) -> bool:
        """
        Delete a record by its primary key.

        Parameters
        ----------
        record_id : object
            Primary key value of the record to delete.

        Returns
        -------
        bool
            ``True`` if a record was deleted, ``False`` if no record matched.
        """
        instance = self.get_by_id(record_id)
        if instance is None:
            return False
        self._session.delete(instance)
        return True
