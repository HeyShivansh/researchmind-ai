"""
Validators for PDF file uploads.

FileStorage assumes it receives validated input; validation is the
responsibility of this module.  Each validator raises
``FileValidationError`` on failure.
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import FileValidationError


class PDFValidator:
    """
    Stateless validator for PDF files.

    Methods are static and intended to be called before passing data
    to ``FileStorage``.
    """

    PDF_MAGIC_BYTES: bytes = b"%PDF"
    ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @staticmethod
    def validate_size(file_bytes: bytes, max_size_mb: int) -> None:
        """
        Check that *file_bytes* does not exceed the configured limit.

        Parameters
        ----------
        file_bytes : bytes
            The raw file content.
        max_size_mb : int
            Maximum allowed size in megabytes.

        Raises
        ------
        FileValidationError
            If the file exceeds *max_size_mb*.
        """
        max_bytes = max_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise FileValidationError(
                "upload",
                f"File exceeds maximum upload size of {max_size_mb} MB",
            )

    @staticmethod
    def validate_extension(filename: str) -> None:
        """
        Check that the filename has an allowed extension.

        Parameters
        ----------
        filename : str
            The name of the uploaded file.

        Raises
        ------
        FileValidationError
            If the extension is not ``.pdf``.
        """
        ext = Path(filename).suffix.lower()
        if ext not in PDFValidator.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                filename,
                f"File extension '{ext}' is not allowed; "
                f"only {', '.join(sorted(PDFValidator.ALLOWED_EXTENSIONS))} "
                f"files are accepted",
            )

    @staticmethod
    def validate_magic_bytes(file_bytes: bytes) -> None:
        """
        Check that the file starts with the PDF magic byte sequence.

        Parameters
        ----------
        file_bytes : bytes
            The raw file content.

        Raises
        ------
        FileValidationError
            If the file does not start with ``%PDF``.
        """
        if not file_bytes.startswith(PDFValidator.PDF_MAGIC_BYTES):
            raise FileValidationError(
                "upload",
                "File does not appear to be a valid PDF "
                "(missing PDF magic bytes)",
            )
