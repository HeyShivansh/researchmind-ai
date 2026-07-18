"""
Data models for processed PDF documents.

Uses ``dataclasses`` for lightweight, immutable, typed structures
that are returned by the processing layer instead of raw dicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentMetadata:
    """
    Metadata extracted from a PDF document.
    Empty-string and whitespace-only values are normalised to ``None``
    by ``DocumentProcessor``.

    Attributes
    ----------
    title : str or None
        Document title from PDF metadata.
    author : str or None
        Document author.
    subject : str or None
        Document subject.
    creator : str or None
        Application that created the document.
    producer : str or None
        Application that produced the PDF.
    page_count : int
        Total number of pages in the document.
    """

    title: str | None
    author: str | None
    subject: str | None
    creator: str | None
    producer: str | None
    page_count: int


@dataclass(frozen=True)
class DocumentPage:
    """
    A single page from a processed PDF document.

    Attributes
    ----------
    page_number : int
        1-based page number.
    text : str
        Full text content extracted from the page, with leading and
        trailing whitespace removed (internal whitespace preserved).
    char_count : int
        Number of characters in the extracted text (after stripping).
    """

    page_number: int
    text: str
    char_count: int = 0


@dataclass(frozen=True)
class ProcessedDocument:
    """
    The complete result of processing a PDF document.

    Attributes
    ----------
    metadata : DocumentMetadata
        Extracted document metadata.
    pages : list[DocumentPage]
        Ordered list of page contents, in reading order.
    """

    metadata: DocumentMetadata
    pages: list[DocumentPage] = field(default_factory=list)
