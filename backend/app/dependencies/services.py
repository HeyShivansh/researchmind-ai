"""
Service dependencies for the ResearchMind AI platform.

Provides FastAPI-compatible dependencies that wire up service layer
instances for injection into route handlers.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.services.paper_service import PaperService

from .database import get_db


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
