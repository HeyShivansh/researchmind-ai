"""
Unit tests for the FileStorage class and PDFValidator.

Tests cover filesystem operations in isolation using ``pytest``'s
built-in ``tmp_path`` fixture.  No PostgreSQL or API dependencies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import FileDeleteError, FileSaveError, FileValidationError
from app.storage.file_storage import FileStorage
from app.storage.validators import PDFValidator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage(tmp_path: Path) -> FileStorage:
    """
    Provide a ``FileStorage`` instance rooted at a temporary directory.

    The temporary directory is automatically cleaned up by pytest
    after each test.
    """
    test_settings = Settings(STORAGE_ROOT=str(tmp_path))
    return FileStorage(test_settings)


# ===================================================================
# Storage directory
# ===================================================================


class TestStorageDirectory:
    """Tests for storage directory initialisation."""

    def test_ensure_storage_directory_created(self, tmp_path: Path) -> None:
        """Verify the papers sub-directory is created on init."""
        papers_dir = tmp_path / "papers"
        assert not papers_dir.exists()

        test_settings = Settings(STORAGE_ROOT=str(tmp_path))
        FileStorage(test_settings)

        assert papers_dir.is_dir()


# ===================================================================
# Save file — FileStorage.save_pdf
# ===================================================================


class TestSaveFile:
    """Tests for ``FileStorage.save_pdf``."""

    def test_save_file_returns_relative_path(
        self, storage: FileStorage
    ) -> None:
        """Verify ``save_pdf`` returns a relative path like ``papers/...``."""
        rel_path = storage.save_pdf(b"PDF content", "test.pdf")

        assert isinstance(rel_path, str)
        assert rel_path.startswith("papers/")
        assert rel_path == "papers/test.pdf"

    def test_save_file_writes_bytes(self, storage: FileStorage) -> None:
        """Verify the saved file contains the exact bytes provided."""
        content = b"%PDF-1.4 sample content"
        storage.save_pdf(content, "sample.pdf")
        papers_dir = Path(storage._root) / "papers"  # type: ignore[attr-defined]

        assert (papers_dir / "sample.pdf").read_bytes() == content

    def test_save_file_creates_file(self, storage: FileStorage) -> None:
        """Verify the file physically exists after saving."""
        storage.save_pdf(b"content", "exists.pdf")
        papers_dir = Path(storage._root) / "papers"  # type: ignore[attr-defined]

        assert (papers_dir / "exists.pdf").is_file()


# ===================================================================
# Filename validation
# ===================================================================


class TestFilenameValidation:
    """Tests for ``FileStorage._validate_filename``."""

    def test_rejects_path_separator(self, storage: FileStorage) -> None:
        """Verify a filename containing ``/`` is rejected."""
        with pytest.raises(FileSaveError, match="path separator"):
            storage.save_pdf(b"content", "subdir/file.pdf")

    def test_rejects_backslash(self, storage: FileStorage) -> None:
        """Verify a filename containing ``\\`` is rejected."""
        with pytest.raises(FileSaveError, match="path separator"):
            storage.save_pdf(b"content", "subdir\\file.pdf")

    def test_rejects_traversal(self, storage: FileStorage) -> None:
        """Verify a filename containing ``..`` is rejected."""
        # ``../malicious.pdf`` is caught by the path-separator check
        # first (``/`` in ``..``), not the traversal check.
        with pytest.raises(FileSaveError, match="path separators"):
            storage.save_pdf(b"content", "../malicious.pdf")

    def test_rejects_empty_filename(self, storage: FileStorage) -> None:
        """Verify an empty filename is rejected."""
        with pytest.raises(FileSaveError, match="empty"):
            storage.save_pdf(b"content", "")


# ===================================================================
# File exists — FileStorage.exists
# ===================================================================


class TestFileExists:
    """Tests for ``FileStorage.exists``."""

    def test_exists_returns_true(self, storage: FileStorage) -> None:
        """Verify ``exists`` returns ``True`` for an existing file."""
        rel_path = storage.save_pdf(b"content", "check.pdf")

        assert storage.exists(rel_path) is True

    def test_exists_returns_false(self, storage: FileStorage) -> None:
        """Verify ``exists`` returns ``False`` for a missing file."""
        assert storage.exists("papers/missing.pdf") is False


# ===================================================================
# Delete file — FileStorage.delete_pdf
# ===================================================================


class TestDeleteFile:
    """Tests for ``FileStorage.delete_pdf``."""

    def test_delete_existing_file(self, storage: FileStorage) -> None:
        """Verify an existing file is removed after deletion."""
        rel_path = storage.save_pdf(b"content", "to-delete.pdf")

        storage.delete_pdf(rel_path)

        assert storage.exists(rel_path) is False

    def test_delete_missing_file_succeeds(self, storage: FileStorage) -> None:
        """Verify deleting a non-existent file does not raise."""
        storage.delete_pdf("papers/missing.pdf")


# ===================================================================
# Delete outside storage root
# ===================================================================


class TestDeleteOutsideRoot:
    """Tests that ``delete_pdf`` rejects paths outside the storage root."""

    def test_rejects_absolute_path_outside_root(
        self, storage: FileStorage
    ) -> None:
        """Verify deleting an absolute path outside the root is rejected."""
        with pytest.raises(FileDeleteError, match="outside storage root"):
            storage.delete_pdf("/etc/passwd")

    def test_rejects_traversal_outside_root(
        self, storage: FileStorage
    ) -> None:
        """Verify a traversal path leaving the root is rejected."""
        with pytest.raises(FileDeleteError, match="outside storage root"):
            storage.delete_pdf("../outside.pdf")

    def test_allows_absolute_path_inside_root(
        self, storage: FileStorage, tmp_path: Path
    ) -> None:
        """Verify an absolute path inside the storage root is allowed."""
        rel_path = storage.save_pdf(b"content", "inside.pdf")
        abs_path = str(tmp_path / "papers" / "inside.pdf")

        storage.delete_pdf(abs_path)

        assert storage.exists(rel_path) is False


# ===================================================================
# PDFValidator — size
# ===================================================================


class TestPDFValidatorSize:
    """Tests for ``PDFValidator.validate_size``."""

    def test_accepts_file_within_limit(self) -> None:
        """Verify a file within the size limit passes."""
        PDFValidator.validate_size(b"a" * 1024, max_size_mb=1)

    def test_rejects_file_exceeding_limit(self) -> None:
        """Verify a file exceeding the size limit raises."""
        with pytest.raises(FileValidationError, match="exceeds maximum"):
            PDFValidator.validate_size(b"a" * (2 * 1024 * 1024), max_size_mb=1)


# ===================================================================
# PDFValidator — extension
# ===================================================================


class TestPDFValidatorExtension:
    """Tests for ``PDFValidator.validate_extension``."""

    def test_accepts_pdf_extension(self) -> None:
        """Verify a ``.pdf`` extension passes."""
        PDFValidator.validate_extension("document.pdf")

    def test_rejects_non_pdf_extension(self) -> None:
        """Verify a ``.txt`` extension raises."""
        with pytest.raises(FileValidationError, match="extension"):
            PDFValidator.validate_extension("document.txt")


# ===================================================================
# PDFValidator — magic bytes
# ===================================================================


class TestPDFValidatorMagicBytes:
    """Tests for ``PDFValidator.validate_magic_bytes``."""

    def test_accepts_pdf_magic_bytes(self) -> None:
        """Verify bytes starting with ``%PDF`` pass."""
        PDFValidator.validate_magic_bytes(b"%PDF-1.4 content")

    def test_rejects_non_pdf_bytes(self) -> None:
        """Verify bytes without ``%PDF`` prefix raise."""
        with pytest.raises(FileValidationError, match="magic bytes"):
            PDFValidator.validate_magic_bytes(b"Not a PDF content")
