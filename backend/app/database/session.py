from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — manages connection pool to PostgreSQL
# ---------------------------------------------------------------------------
# Pool configuration:
#   pool_size=5      — 5 connections kept open and ready
#   max_overflow=10  — up to 10 extra connections allowed under load
#   pool_timeout=30  — seconds to wait for a connection before raising an error
#   pool_recycle=1800— recycle connections older than 30 min to avoid stale
#                      connections behind NAT / load balancers
#   echo=False       — set True in config to log all SQL statements
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
)

# ---------------------------------------------------------------------------
# SessionLocal — thread-local session factory
# ---------------------------------------------------------------------------
# Each call to SessionLocal() returns a new Session bound to the engine.
# Use autocommit=False (default) so that changes must be explicitly
# committed — this avoids accidental data loss and keeps transactions safe.
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage in a route:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...

    The session is opened when the dependency is resolved and **always**
    closed when the request finishes — even if an exception is raised —
    thanks to the try/finally block.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
