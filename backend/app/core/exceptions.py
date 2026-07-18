"""
Application-level exceptions for the ResearchMind AI platform.

Defines exception types used by infrastructure layers such as
storage, ingestion, and retrieval.
"""


class StorageError(Exception):
    """
    Base exception for all storage-related errors.

    All concrete storage exceptions should inherit from this class.
    """


class FileSaveError(StorageError):
    """
    Raised when a file cannot be saved to the storage layer.

    Parameters
    ----------
    filename : str
        The name of the file that could not be saved.
    reason : str
        A description of why the save failed.
    """

    def __init__(self, filename: str, reason: str = "") -> None:
        self.filename = filename
        self.reason = reason
        message = f"Failed to save file '{filename}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class FileDeleteError(StorageError):
    """
    Raised when a file cannot be deleted from the storage layer.

    Parameters
    ----------
    path : str
        The path of the file that could not be deleted.
    reason : str
        A description of why the delete failed.
    """

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        self.reason = reason
        message = f"Failed to delete file '{path}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class FileValidationError(StorageError):
    """
    Raised when a file fails validation checks (size, extension, magic bytes).

    Parameters
    ----------
    filename : str
        The name of the file that failed validation.
    reason : str
        A description of the validation failure.
    """

    def __init__(self, filename: str, reason: str) -> None:
        self.filename = filename
        self.reason = reason
        super().__init__(f"File validation failed for '{filename}': {reason}")


class ProcessingError(Exception):
    """
    Base exception for all document processing errors.

    All concrete processing exceptions should inherit from this class.
    """


class InvalidPDFError(ProcessingError):
    """
    Raised when a PDF file cannot be opened or is not a valid PDF.

    Parameters
    ----------
    path : str
        The path to the file that could not be opened.
    reason : str
        A description of why the file is invalid.
    """

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        self.reason = reason
        message = f"Invalid PDF '{path}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class DocumentProcessingError(ProcessingError):
    """
    Raised when an error occurs during document text extraction.

    Parameters
    ----------
    path : str
        The path to the document being processed.
    reason : str
        A description of the error.
    """

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        self.reason = reason
        message = f"Failed to process document '{path}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
