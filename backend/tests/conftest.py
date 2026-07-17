"""
Pytest configuration and fixtures for integration testing.

Provides an isolated PostgreSQL test database with per-test session
management, FastAPI dependency overrides, and reusable test data.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.dependencies import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------------------------
# Points to a dedicated database that must be created externally (e.g. via
# Docker Compose or CI setup).  Tests never touch the production database.
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = (
    "postgresql+psycopg://researchmind:researchmind"
    "@localhost:5432/researchmind_test"
)

# ---------------------------------------------------------------------------
# Session-scoped engine
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """
    Create a SQLAlchemy engine connected to the test database.

    All tables are created before the test session starts and dropped
    after it finishes.
    """
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# Per-test session with transaction rollback
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """
    Provide a fresh database session for each test.

    The session is wrapped in a transaction that is **rolled back**
    when the test finishes, ensuring complete isolation between tests
    without the overhead of re-creating tables.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient with dependency override
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI TestClient that uses the test database session.

    The ``get_db`` dependency is overridden to inject ``db_session``
    instead of the production database session.  The override is
    removed after each test.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
