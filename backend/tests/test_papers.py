"""
Integration tests for the Paper API.

Tests cover the complete request lifecycle:
    HTTP → FastAPI → DI → Service → Repository → Database

No mocking is used.  All tests run against a real PostgreSQL database
with per-test transaction rollback for isolation.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_paper(
    client: TestClient,
    overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    """
    Create a paper via ``POST /papers`` and return the response data and
    status code.

    Parameters
    ----------
    client : TestClient
        The test API client.
    overrides : dict[str, Any] | None
        Optional fields to override the default payload.

    Returns
    -------
    tuple[dict[str, Any], int]
        The response JSON body and HTTP status code.
    """
    payload = {
        "title": "Default Test Paper",
        "pdf_path": "/papers/default.pdf",
    }
    if overrides:
        payload.update(overrides)

    response = client.post("/papers", json=payload)
    return response.json(), response.status_code


def assert_valid_paper(data: dict[str, Any]) -> None:
    """Assert that *data* contains all expected Paper response fields."""
    assert UUID(data["id"])
    assert isinstance(data["title"], str)
    assert isinstance(data["pdf_path"], str)
    assert "created_at" in data
    assert "updated_at" in data


# ===================================================================
# Health
# ===================================================================


class TestHealth:
    """Tests for the root health-check endpoint."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Verify ``GET /`` returns the expected health payload."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {
            "message": "ResearchMind AI API",
            "status": "running",
        }


# ===================================================================
# Create paper — POST /papers
# ===================================================================


class TestCreatePaper:
    """Tests for ``POST /papers``."""

    def test_created_status(self, client: TestClient) -> None:
        """Verify a valid paper creation returns 201 Created."""
        data, status = create_paper(client)

        assert status == 201
        assert_valid_paper(data)

    def test_returns_all_fields(self, client: TestClient) -> None:
        """Verify all submitted fields are echoed back."""
        payload = {
            "title": "Quantum Algorithms",
            "abstract": "An overview of quantum algorithms.",
            "doi": "10.1234/quantum-algo",
            "publication_year": 2025,
            "pdf_path": "/papers/quantum.pdf",
        }

        data, _ = create_paper(client, overrides=payload)

        assert data["title"] == "Quantum Algorithms"
        assert data["abstract"] == "An overview of quantum algorithms."
        assert data["doi"] == "10.1234/quantum-algo"
        assert data["publication_year"] == 2025
        assert data["pdf_path"] == "/papers/quantum.pdf"

    def test_returns_uuid(self, client: TestClient) -> None:
        """Verify the returned ``id`` is a valid UUID."""
        data, status = create_paper(client)

        assert status == 201
        assert UUID(data["id"])

    def test_returns_timestamps(self, client: TestClient) -> None:
        """Verify ``created_at`` and ``updated_at`` are present."""
        data, status = create_paper(client)

        assert status == 201
        assert "created_at" in data
        assert "updated_at" in data

    def test_duplicate_doi_returns_409(self, client: TestClient) -> None:
        """Verify a paper with a duplicate DOI returns 409 Conflict."""
        doi = "10.1234/unique-doi-409"

        data, status = create_paper(client, overrides={"doi": doi})
        assert status == 201

        data, status = create_paper(client, overrides={"doi": doi})
        assert status == 409
        assert "already exists" in data["detail"]


# ===================================================================
# List papers — GET /papers
# ===================================================================


class TestListPapers:
    """Tests for ``GET /papers``."""

    def test_empty_database(self, client: TestClient) -> None:
        """Verify an empty database returns an empty list."""
        response = client.get("/papers")

        assert response.status_code == 200
        assert response.json() == []

    def test_single_paper(self, client: TestClient) -> None:
        """Verify listing returns one paper after a single creation."""
        create_paper(client)

        response = client.get("/papers")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_multiple_papers(self, client: TestClient) -> None:
        """Verify listing returns all created papers."""
        create_paper(client, overrides={"title": "Paper A"})
        create_paper(client, overrides={"title": "Paper B"})
        create_paper(client, overrides={"title": "Paper C"})

        response = client.get("/papers")

        assert response.status_code == 200
        papers = response.json()
        assert len(papers) == 3
        titles = {p["title"] for p in papers}
        assert titles == {"Paper A", "Paper B", "Paper C"}


# ===================================================================
# Pagination — GET /papers?skip=&limit=
# ===================================================================


class TestListPapersPagination:
    """Tests for paginated ``GET /papers``."""

    def _seed(self, client: TestClient, count: int = 3) -> None:
        """Create *count* papers for pagination tests."""
        for i in range(count):
            create_paper(
                client,
                overrides={
                    "title": f"Paper {i}",
                    "doi": f"10.1234/pagination-{i}",
                },
            )

    def test_skip_first_page(self, client: TestClient) -> None:
        """Verify ``skip=1`` excludes the first paper."""
        self._seed(client, count=3)

        response = client.get("/papers?skip=1")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_limit_page_size(self, client: TestClient) -> None:
        """Verify ``limit=1`` returns only one paper."""
        self._seed(client, count=3)

        response = client.get("/papers?limit=1")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_skip_beyond_total(self, client: TestClient) -> None:
        """Verify ``skip`` beyond total papers returns an empty list."""
        self._seed(client, count=2)

        response = client.get("/papers?skip=10")

        assert response.status_code == 200
        assert response.json() == []

    def test_zero_limit(self, client: TestClient) -> None:
        """Verify ``limit=0`` returns zero papers."""
        self._seed(client, count=2)

        response = client.get("/papers?limit=0")

        assert response.status_code == 200
        assert response.json() == []


# ===================================================================
# Get paper — GET /papers/{paper_id}
# ===================================================================


class TestGetPaper:
    """Tests for ``GET /papers/{paper_id}``."""

    def test_existing_paper(self, client: TestClient) -> None:
        """Verify an existing paper can be retrieved by its ID."""
        payload = {
            "title": "Retrieval Paper",
            "abstract": "Abstract for retrieval.",
            "doi": "10.1234/retrieval",
            "publication_year": 2023,
            "pdf_path": "/papers/retrieval.pdf",
        }
        created, status = create_paper(client, overrides=payload)
        assert status == 201

        response = client.get(f"/papers/{created['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == "Retrieval Paper"
        assert data["abstract"] == "Abstract for retrieval."
        assert data["doi"] == "10.1234/retrieval"
        assert data["publication_year"] == 2023
        assert data["pdf_path"] == "/papers/retrieval.pdf"

    def test_not_found(self, client: TestClient) -> None:
        """Verify a non-existent paper ID returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/papers/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ===================================================================
# Validation — 422 Unprocessable Entity
# ===================================================================


class TestValidation:
    """Tests for request validation errors (422)."""

    def test_empty_body(self, client: TestClient) -> None:
        """Verify an empty request body returns 422."""
        response = client.post("/papers", json={})

        assert response.status_code == 422

    def test_missing_title(self, client: TestClient) -> None:
        """Verify omitting required field ``title`` returns 422."""
        response = client.post(
            "/papers",
            json={"pdf_path": "/papers/no-title.pdf"},
        )

        assert response.status_code == 422

    def test_missing_pdf_path(self, client: TestClient) -> None:
        """Verify omitting required field ``pdf_path`` returns 422."""
        response = client.post(
            "/papers",
            json={"title": "No PDF Path"},
        )

        assert response.status_code == 422

    def test_invalid_publication_year_type(self, client: TestClient) -> None:
        """Verify a string ``publication_year`` returns 422."""
        response = client.post(
            "/papers",
            json={
                "title": "Bad Year",
                "pdf_path": "/papers/bad-year.pdf",
                "publication_year": "not-a-number",
            },
        )

        assert response.status_code == 422

    def test_invalid_uuid(self, client: TestClient) -> None:
        """Verify a non-UUID paper ID returns 422."""
        response = client.get("/papers/not-a-uuid")

        assert response.status_code == 422

    def test_title_too_long(self, client: TestClient) -> None:
        """Verify a title exceeding the 500-char limit returns 422."""
        response = client.post(
            "/papers",
            json={
                "title": "X" * 501,
                "pdf_path": "/papers/long-title.pdf",
            },
        )

        assert response.status_code == 422


# ===================================================================
# Database isolation
# ===================================================================


class TestDatabaseIsolation:
    """Verify each test starts with a clean database."""

    def test_isolation_one(self, client: TestClient) -> None:
        """First isolation check — database is empty."""
        response = client.get("/papers")
        assert response.json() == []

        # Create a paper so the next test can detect cross-contamination.
        create_paper(client)

    def test_isolation_two(self, client: TestClient) -> None:
        """Second isolation check — paper from previous test is gone."""
        response = client.get("/papers")
        assert response.json() == []
