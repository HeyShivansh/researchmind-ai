"""
File storage abstraction for the ResearchMind AI platform.

Provides a clean interface for saving, deleting, and checking the
existence of files without exposing filesystem details to the rest
of the application.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import FileDeleteError, FileSaveError


class FileStorage:
    """
    Abstraction over the local filesystem for storing uploaded files.

    All file operations go through this class so that the rest of the
    application never interacts with ``pathlib`` or ``os`` directly.

    Parameters
    ----------
    settings : Settings
        Application settings providing storage root and papers
        directory configuration.

    Examples
    --------
    >>> from app.core.config import settings
    >>> storage = FileStorage(settings)
    >>> rel_path = storage.save_pdf(b"%PDF-content", "paper.pdf")
    >>> storage.exists(rel_path)
    True
    >>> storage.delete_pdf(rel_path)
    """

    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.STORAGE_ROOT).resolve()
        self._papers_subdir = settings.PAPERS_DIRECTORY
        self.ensure_storage_exists()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def root(self) -> Path:
        """Return the resolved absolute path to the storage root directory."""
        return self._root

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_pdf(self, file_bytes: bytes, filename: str) -> str:
        """
        Save a PDF file to the storage layer.

        Parameters
        ----------
        file_bytes : bytes
            Raw bytes of the PDF file.
        filename : str
            The final filename to use (caller is responsible for
            generating a unique name).  Must not contain path
            separators or traversal sequences.

        Returns
        -------
        str
            A relative storage path (e.g. ``papers/xxxx.pdf``).

        Raises
        ------
        FileSaveError
            If *filename* is invalid or the file could not be written.
        """
        self._validate_filename(filename)
        dest = self._papers_dir / filename
        try:
            dest.write_bytes(file_bytes)
        except OSError as exc:
            raise FileSaveError(filename, str(exc)) from exc
        return f"{self._papers_subdir}/{filename}"

    def delete_pdf(self, storage_path: str) -> None:
        """
        Delete a file from the storage layer.

        Only files located inside the configured storage root can be
        deleted.  If the file does not exist the operation succeeds
        silently.

        Parameters
        ----------
        storage_path : str
            A relative storage path (e.g. ``papers/xxxx.pdf``).

        Raises
        ------
        FileDeleteError
            If the path points outside the storage root or the file
            exists but could not be deleted.
        """
        target = self._resolve_within_root(storage_path)
        if not target.exists():
            return
        try:
            target.unlink()
        except OSError as exc:
            raise FileDeleteError(storage_path, str(exc)) from exc

    def exists(self, storage_path: str) -> bool:
        """
        Check whether a file exists in the storage layer.

        Parameters
        ----------
        storage_path : str
            A relative storage path (e.g. ``papers/xxxx.pdf``).

        Returns
        -------
        bool
            ``True`` if the file exists, ``False`` otherwise.
        """
        try:
            target = self._resolve_within_root(storage_path)
        except FileDeleteError:
            return False
        return target.is_file()

    def ensure_storage_exists(self) -> None:
        """Create the storage directory hierarchy if it does not exist."""
        self._papers_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @property
    def _papers_dir(self) -> Path:
        """Return the resolved absolute path to the papers directory."""
        return self._root / self._papers_subdir

    def _resolve_within_root(self, storage_path: str) -> Path:
        """
        Resolve a storage path to an absolute path and verify it lies
        inside the configured storage root.

        Uses ``Path.relative_to()`` to guarantee the resolved path is
        an actual descendant of the root — avoids string-prefix
        matching vulnerabilities.

        Parameters
        ----------
        storage_path : str
            Path relative to the storage root, or an absolute path.

        Returns
        -------
        Path
            The resolved absolute path.

        Raises
        ------
        FileDeleteError
            If the resolved path is outside the storage root.
        """
        candidate = Path(storage_path)
        if not candidate.is_absolute():
            candidate = self._root / candidate
        resolved = candidate.resolve()

        try:
            resolved.relative_to(self._root)
        except ValueError as exc:
            raise FileDeleteError(
                storage_path,
                f"Path resolves outside storage root '{self._root}'",
            ) from exc
        return resolved

    @staticmethod
    def _validate_filename(filename: str) -> None:
        """
        Validate that a filename is safe for storage.

        Rejects empty filenames, filenames containing path separators,
        and filenames with path-traversal sequences.

        Parameters
        ----------
        filename : str
            The filename to validate.

        Raises
        ------
        FileSaveError
            If the filename is invalid.
        """
        if not filename:
            raise FileSaveError(filename, "Filename must not be empty")
        if "/" in filename or "\\" in filename:
            raise FileSaveError(
                filename, "Filename must not contain path separators"
            )
        if ".." in filename:
            raise FileSaveError(
                filename,
                "Filename must not contain path traversal sequences",
            )
