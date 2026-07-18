"""
Integration tests for the PDF upload endpoint.

Tests cover the complete upload lifecycle including validation,
file persistence, database recording, and error recovery.
"""

from __future__ import annotations

import io
from collections.abc import Generator
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.dependencies import get_file_storage
from app.main import app
from app.storage.file_storage import FileStorage

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    """Provide the root directory for file storage during upload tests."""
    papers_dir = tmp_path / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture()
def client_with_storage(
    client: TestClient, storage_root: Path
) -> Generator[TestClient, None, None]:
    """
    Provide a TestClient that overrides both database and file-storage
    dependencies to use isolated temporary locations.
    """
    test_settings = Settings(STORAGE_ROOT=str(storage_root))
    test_storage = FileStorage(test_settings)
    app.dependency_overrides[get_file_storage] = lambda: test_storage
    yield client
    # Only remove the key we added — the client fixture handles the rest.
    app.dependency_overrides.pop(get_file_storage, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf_bytes(text: str = "Hello, world!") -> bytes:
    """Create a real single-page PDF in memory and return its bytes."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), text, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


PDF_BYTES = _make_pdf_bytes()


def _upload(
    client: TestClient,
    file_bytes: bytes = PDF_BYTES,
    filename: str = "paper.pdf",
    **metadata: str | int | None,
) -> tuple[dict, int]:
    """Upload a PDF with optional metadata and return (json, status).

    Catches both network-level and server-level exceptions so callers
    can assert on status codes without worrying about how the TestClient
    propagates errors.
    """
    files = {"file": (filename, io.BytesIO(file_bytes), "application/pdf")}
    # Convert all metadata values to strings for multipart form data.
    data = {k: str(v) for k, v in metadata.items() if v is not None}
    try:
        response = client.post("/papers/upload", files=files, data=data)
    except Exception:
        return {}, 500
    try:
        return response.json(), response.status_code
    except Exception:
        return {}, response.status_code


# ===================================================================
# Successful upload
# ===================================================================


class TestSuccessfulUpload:
    """Tests for a valid PDF upload."""

    def test_returns_201(self, client_with_storage: TestClient) -> None:
        """Verify a valid upload returns 201 Created."""
        _, status = _upload(client_with_storage)
        assert status == 201

    def test_returns_paper_response(
        self, client_with_storage: TestClient
    ) -> None:
        """Verify the response contains PaperResponse fields."""
        data, status = _upload(
            client_with_storage,
            title="Uploaded Paper",
            doi="10.1234/upload-test",
            publication_year=2024,
            abstract="Uploaded paper abstract.",
        )
        assert status == 201
        assert data["title"] == "Uploaded Paper"
        assert data["doi"] == "10.1234/upload-test"
        assert data["publication_year"] == 2024
        assert data["abstract"] == "Uploaded paper abstract."
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_pdf_stored_on_disk(
        self, client_with_storage: TestClient, storage_root: Path
    ) -> None:
        """Verify the uploaded PDF is saved to the storage directory."""
        data, status = _upload(client_with_storage)
        assert status == 201

        storage_path: str = data["pdf_path"]
        papers_dir = storage_root / "papers"
        assert (papers_dir / Path(storage_path).name).is_file()

    def test_metadata_stored_in_database(
        self, client_with_storage: TestClient
    ) -> None:
        """Verify the paper can be retrieved after upload."""
        data, status = _upload(
            client_with_storage,
            title="Persistent Paper",
            doi="10.1234/persist",
        )
        assert status == 201
        paper_id = data["id"]

        response = client_with_storage.get(f"/papers/{paper_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Persistent Paper"


# ===================================================================
# Duplicate DOI
# ===================================================================


class TestDuplicateDOI:
    """Tests for duplicate DOI handling."""

    def test_duplicate_doi_returns_409(
        self, client_with_storage: TestClient
    ) -> None:
        """Verify uploading a second PDF with the same DOI returns 409."""
        _, status = _upload(
            client_with_storage,
            title="First",
            doi="10.1234/dup-doi",
        )
        assert status == 201

        data, status = _upload(
            client_with_storage,
            title="Second",
            doi="10.1234/dup-doi",
        )
        assert status == 409
        assert "already exists" in data["detail"]


# ===================================================================
# Validation errors
# ===================================================================


class TestValidationErrors:
    """Tests for file validation failures."""

    def test_invalid_extension(
        self, client_with_storage: TestClient
    ) -> None:
        """Verify a non-PDF extension returns 422."""
        _, status = _upload(client_with_storage, filename="document.txt")
        assert status == 422

    def test_invalid_magic_bytes(
        self, client_with_storage: TestClient
    ) -> None:
        """Verify a file without PDF magic bytes returns 422."""
        _, status = _upload(
            client_with_storage, file_bytes=b"Not a PDF content"
        )
        assert status == 422

    def test_oversized_upload(
        self, client_with_storage: TestClient
    ) -> None:
        """Verify a file exceeding the size limit returns 422."""
        big = b"X" * (51 * 1024 * 1024)  # 51 MB > default 50 MB limit
        _, status = _upload(client_with_storage, file_bytes=big)
        assert status == 422


# ===================================================================
# Rollback behaviour
# ===================================================================


class TestRollback:
    """Tests for atomic rollback on failure."""

    def test_rollback_deletes_uploaded_file(
        self, client_with_storage: TestClient, storage_root: Path
    ) -> None:
        """Verify that a failed DB insert cleans up the saved file."""
        # First upload to create the DOI.
        _, status = _upload(
            client_with_storage,
            title="Original",
            doi="10.1234/rollback-file",
        )
        assert status == 201

        # Second upload with the same DOI — DB insert fails,
        # file should be cleaned up.
        _, status = _upload(
            client_with_storage,
            title="Duplicate",
            doi="10.1234/rollback-file",
        )
        assert status == 409

        # Only the first upload's file should remain on disk.
        papers_dir = storage_root / "papers"
        files_after = list(papers_dir.iterdir())
        assert len(files_after) == 1

    def test_commit_failure_deletes_uploaded_file(
        self,
        client_with_storage: TestClient,
        storage_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify that a commit failure after file save cleans up both
        the database record and the uploaded file."""
        # -- Arrange -------------------------------------------------------
        papers_dir = storage_root / "papers"
        files_before = list(papers_dir.iterdir())

        def failing_commit(self: Session) -> None:
            """Replacement for ``Session.commit`` that raises an error."""
            raise SQLAlchemyError("Simulated commit failure")

        monkeypatch.setattr(Session, "commit", failing_commit)

        # -- Act -----------------------------------------------------------
        data, status = _upload(
            client_with_storage,
            title="Atomicity Test",
            doi="10.1234/atomic-test",
        )

        # -- Assert --------------------------------------------------------
        # The service re-raises the exception, so FastAPI returns 500.
        assert status == 500

        # The uploaded file should have been deleted by the rollback handler.
        files_after = list(papers_dir.iterdir())
        assert files_after == files_before

        # No Paper row should exist in the database.
        response = client_with_storage.get("/papers")
        assert response.json() == []
