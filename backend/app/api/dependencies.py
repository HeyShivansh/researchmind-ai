"""
FastAPI dependency injection for the ResearchMind AI platform.

Provides reusable dependencies that wire up the database session and
service layer for injection into route handlers.
"""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.paper_service import PaperService


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    The session is opened when the dependency is resolved and **always**
    closed when the request finishes — even if an exception is raised —
    thanks to the try/finally block.

    Yields
    ------
    Session
        A SQLAlchemy ORM session bound to the engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_paper_service(
    db: Session = Depends(get_db),
) -> PaperService:
    """
    FastAPI dependency that provides a ``PaperService`` instance.

    Parameters
    ----------
    db : Session
        Database session obtained from ``get_db``.

    Returns
    -------
    PaperService
        A service instance wired to the provided database session.
    """
    return PaperService(db)
