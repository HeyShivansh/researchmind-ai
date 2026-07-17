"""
Database session dependency for the ResearchMind AI platform.

Provides a FastAPI-compatible dependency that creates a SQLAlchemy
session per request and ensures it is always closed.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.session import SessionLocal


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
