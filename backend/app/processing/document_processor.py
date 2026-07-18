"""
Document processor for PDF text extraction.

Provides the ``DocumentProcessor`` class which wraps PyMuPDF (fitz)
and returns domain models rather than raw fitz objects.  All
library-specific types are hidden behind this abstraction.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from app.core.exceptions import DocumentProcessingError, InvalidPDFError

from .models import DocumentMetadata, DocumentPage, ProcessedDocument


class DocumentProcessor:
    """
    Processor for extracting structured content from PDF files.

    Uses PyMuPDF internally but returns only application-level
    dataclass models.  No ``fitz`` types are exposed to callers.

    Examples
    --------
    >>> from pathlib import Path
    >>> processor = DocumentProcessor()
    >>> result = processor.process(Path(\"/path/to/document.pdf\"))
    >>> result.metadata.page_count
    3
    >>> result.pages[0].text
    '...'
    """

    def process(self, pdf_path: Path) -> ProcessedDocument:
        """
        Open a PDF, extract metadata and text from every page.

        Parameters
        ----------
        pdf_path : Path
            Path to the PDF file to process.

        Returns
        -------
        ProcessedDocument
            Structured result containing metadata and page texts.

        Raises
        ------
        InvalidPDFError
            If the file cannot be opened or is not a valid PDF.
        DocumentProcessingError
            If text extraction fails after the document is opened.
        """
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as exc:
            raise InvalidPDFError(
                str(pdf_path),
                f"Cannot open PDF: {exc}",
            ) from exc

        with doc:
            try:
                metadata = self._extract_metadata(doc)
                pages = self._extract_pages(doc)
                return ProcessedDocument(metadata=metadata, pages=pages)
            except Exception as exc:
                raise DocumentProcessingError(
                    str(pdf_path),
                    f"Extraction failed: {exc}",
                ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_metadata_value(value: str | None) -> str | None:
        """
        Convert empty or whitespace-only strings to ``None``.

        Parameters
        ----------
        value : str or None
            Raw metadata value from PyMuPDF.

        Returns
        -------
        str or None
            The original value if non-empty, otherwise ``None``.
        """
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None

    @staticmethod
    def _extract_metadata(doc: fitz.Document) -> DocumentMetadata:
        """
        Build a ``DocumentMetadata`` from a fitz document's metadata dict.

        Empty-string and whitespace-only metadata values are normalised
        to ``None``.

        Parameters
        ----------
        doc : fitz.Document
            An opened PyMuPDF document.

        Returns
        -------
        DocumentMetadata
            Extracted metadata with missing fields set to ``None``.
        """
        raw = doc.metadata or {}
        return DocumentMetadata(
            title=DocumentProcessor._normalize_metadata_value(raw.get("title")),
            author=DocumentProcessor._normalize_metadata_value(raw.get("author")),
            subject=DocumentProcessor._normalize_metadata_value(raw.get("subject")),
            creator=DocumentProcessor._normalize_metadata_value(raw.get("creator")),
            producer=DocumentProcessor._normalize_metadata_value(raw.get("producer")),
            page_count=doc.page_count,
        )

    @staticmethod
    def _extract_pages(doc: fitz.Document) -> list[DocumentPage]:
        """
        Extract text from every page in the document.

        Leading and trailing whitespace is removed from each page's
        text (internal whitespace is preserved).  Each page also
        carries its character count.

        Pages are returned in reading order (1-based numbering).

        Parameters
        ----------
        doc : fitz.Document
            An opened PyMuPDF document.

        Returns
        -------
        list[DocumentPage]
            One ``DocumentPage`` per page, each with full-page text.
        """
        pages: list[DocumentPage] = []
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            pages.append(
                DocumentPage(
                    page_number=page_number,
                    text=text,
                    char_count=len(text),
                )
            )
        return pages
