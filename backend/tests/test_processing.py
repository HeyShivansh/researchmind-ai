"""
Unit tests for the DocumentProcessor and processing models.

Tests use real PDF files generated during test execution via
PyMuPDF.  No mocking, no database, no FastAPI.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.core.exceptions import InvalidPDFError
from app.processing import DocumentProcessor, ProcessedDocument
from app.processing.models import DocumentMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf(path: Path, text: str = "Hello, world!") -> Path:
    """Create a simple single-page PDF at *path* and return the path."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def _make_multi_page_pdf(path: Path, page_count: int = 3) -> Path:
    """Create a multi-page PDF with one line of text per page."""
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text(
            fitz.Point(72, 72), f"Page {i + 1} content", fontsize=12
        )
    doc.save(str(path))
    doc.close()
    return path


def _make_pdf_with_metadata(path: Path) -> Path:
    """Create a PDF with metadata fields populated."""
    doc = fitz.open()
    doc.set_metadata(
        {
            "title": "Test Document",
            "author": "Test Author",
            "subject": "Test Subject",
            "creator": "Test Creator",
            "producer": "Test Producer",
        }
    )
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), "Metadata test", fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def _make_pdf_with_empty_metadata(path: Path) -> Path:
    """Create a PDF whose metadata values are empty strings."""
    doc = fitz.open()
    doc.set_metadata(
        {
            "title": "",
            "author": "",
            "subject": "   ",
            "creator": "",
            "producer": "",
        }
    )
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), "Empty metadata", fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture()
def processor() -> DocumentProcessor:
    """Provide a fresh DocumentProcessor instance."""
    return DocumentProcessor()


# ===================================================================
# Successful extraction
# ===================================================================


class TestSuccessfulExtraction:
    """Tests for basic PDF text extraction."""

    def test_returns_processed_document(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify ``process`` returns a ``ProcessedDocument``."""
        pdf = _make_pdf(tmp_path / "simple.pdf")
        result = processor.process(pdf)
        assert isinstance(result, ProcessedDocument)

    def test_extracts_text(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify the extracted text matches the input."""
        pdf = _make_pdf(tmp_path / "text.pdf", text="Custom content")
        result = processor.process(pdf)
        assert "Custom content" in result.pages[0].text

    def test_preserves_page_order(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify multi-page text appears in the correct order."""
        pdf = _make_multi_page_pdf(tmp_path / "multi.pdf", page_count=3)
        result = processor.process(pdf)
        assert len(result.pages) == 3
        assert "Page 1 content" in result.pages[0].text
        assert "Page 2 content" in result.pages[1].text
        assert "Page 3 content" in result.pages[2].text


# ===================================================================
# Metadata extraction
# ===================================================================


class TestMetadataExtraction:
    """Tests for PDF metadata extraction."""

    def test_returns_metadata(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify the result contains a ``DocumentMetadata``."""
        pdf = _make_pdf(tmp_path / "meta.pdf")
        result = processor.process(pdf)
        assert isinstance(result.metadata, DocumentMetadata)

    def test_extracts_metadata_fields(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify all standard metadata fields are extracted."""
        pdf = _make_pdf_with_metadata(tmp_path / "full-meta.pdf")
        result = processor.process(pdf)
        meta = result.metadata
        assert meta.title == "Test Document"
        assert meta.author == "Test Author"
        assert meta.subject == "Test Subject"
        assert meta.creator == "Test Creator"
        assert meta.producer == "Test Producer"

    def test_empty_metadata_becomes_none(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify empty-string metadata values are normalized to ``None``."""
        pdf = _make_pdf_with_empty_metadata(tmp_path / "empty-meta.pdf")
        result = processor.process(pdf)
        meta = result.metadata
        assert meta.title is None
        assert meta.author is None
        assert meta.subject is None
        assert meta.creator is None
        assert meta.producer is None

    def test_extracts_page_count(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify ``page_count`` matches the number of pages."""
        pdf = _make_multi_page_pdf(tmp_path / "pages.pdf", page_count=5)
        result = processor.process(pdf)
        assert result.metadata.page_count == 5


# ===================================================================
# Multiple pages
# ===================================================================


class TestMultiplePages:
    """Tests for multi-page document handling."""

    def test_all_pages_returned(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify every page is present in the result."""
        pdf = _make_multi_page_pdf(tmp_path / "ten.pdf", page_count=10)
        result = processor.process(pdf)
        assert len(result.pages) == 10

    def test_page_numbers_are_sequential(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify page numbers start at 1 and are sequential."""
        pdf = _make_multi_page_pdf(tmp_path / "seq.pdf", page_count=4)
        result = processor.process(pdf)
        numbers = [p.page_number for p in result.pages]
        assert numbers == [1, 2, 3, 4]


# ===================================================================
# Page text normalization
# ===================================================================


class TestPageTextNormalization:
    """Tests for text stripping behaviour."""

    def test_page_text_is_stripped(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify leading and trailing whitespace is removed from page text."""
        pdf = tmp_path / "whitespace.pdf"
        doc = fitz.open()
        page = doc.new_page()
        # Insert text surrounded by whitespace.
        page.insert_text(fitz.Point(72, 72), "  Content with spaces  ", fontsize=12)
        doc.save(str(pdf))
        doc.close()

        result = processor.process(pdf)
        assert result.pages[0].text == "Content with spaces"

    def test_internal_whitespace_preserved(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify internal whitespace is not removed."""
        pdf = tmp_path / "internal.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            fitz.Point(72, 72), "Line1\n\n  Line2\nLine3", fontsize=12
        )
        doc.save(str(pdf))
        doc.close()

        result = processor.process(pdf)
        assert "Line1" in result.pages[0].text
        assert "Line2" in result.pages[0].text
        assert "Line3" in result.pages[0].text


# ===================================================================
# char_count
# ===================================================================


class TestCharCount:
    """Tests for the ``char_count`` field on ``DocumentPage``."""

    def test_char_count_matches_stripped_text(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify ``char_count`` equals the length of stripped text."""
        pdf = _make_pdf(tmp_path / "char.pdf", text="Hello!")
        result = processor.process(pdf)
        assert result.pages[0].char_count == 6  # len("Hello!")

    def test_char_count_empty_page(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify a blank page has a ``char_count`` of ``0``."""
        pdf = tmp_path / "blank.pdf"
        doc = fitz.open()
        doc.new_page()  # Page with no text.
        doc.save(str(pdf))
        doc.close()

        result = processor.process(pdf)
        assert result.pages[0].char_count == 0


# ===================================================================
# Empty PDF
# ===================================================================


class TestEmptyPDF:
    """Tests for empty (zero-page) PDF handling."""

    def test_no_pages(self, tmp_path: Path, processor: DocumentProcessor) -> None:
        """Verify a zero-page PDF returns an empty pages list."""
        pdf = tmp_path / "empty.pdf"
        # PyMuPDF cannot save a PDF with zero pages, so we construct
        # a minimal valid zero-page PDF manually.
        zero_page_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
            b"xref\n0 3\n0000000000 65535 f \n"
            b"0000000009 00000 n \n0000000058 00000 n \n"
            b"trailer\n<< /Size 3 /Root 1 0 R >>\n"
            b"startxref\n100\n%%EOF\n"
        )
        pdf.write_bytes(zero_page_pdf)

        result = processor.process(pdf)
        assert result.pages == []
        assert result.metadata.page_count == 0


# ===================================================================
# Invalid / corrupted PDF
# ===================================================================


class TestInvalidPDF:
    """Tests for error handling with invalid or corrupted files."""

    def test_non_existent_file(self, processor: DocumentProcessor) -> None:
        """Verify a non-existent path raises ``InvalidPDFError``."""
        with pytest.raises(InvalidPDFError, match="Cannot open"):
            processor.process(Path("/nonexistent/file.pdf"))

    def test_not_a_pdf(self, tmp_path: Path, processor: DocumentProcessor) -> None:
        """Verify a non-PDF file raises ``InvalidPDFError``."""
        not_pdf = tmp_path / "not.pdf"
        not_pdf.write_text("This is not a PDF file.")

        with pytest.raises(InvalidPDFError, match="Cannot open"):
            processor.process(not_pdf)

    def test_corrupted_pdf(
        self, tmp_path: Path, processor: DocumentProcessor
    ) -> None:
        """Verify a corrupted PDF raises ``InvalidPDFError``."""
        corrupted = tmp_path / "corrupted.pdf"
        corrupted.write_bytes(b"%PDF-1.4 garbage\x00\xFFdata")

        with pytest.raises(InvalidPDFError, match="Cannot open"):
            processor.process(corrupted)


# ===================================================================
# Model immutability
# ===================================================================


class TestModelImmutability:
    """Tests that processing dataclasses are immutable."""

    def test_metadata_is_frozen(self) -> None:
        """Verify ``DocumentMetadata`` cannot be modified after creation."""
        meta = DocumentMetadata(
            title="Test", author=None, subject=None,
            creator=None, producer=None, page_count=1,
        )
        with pytest.raises(AttributeError):
            meta.title = "Changed"  # type: ignore[misc]

    def test_processed_document_is_frozen(self) -> None:
        """Verify ``ProcessedDocument`` cannot be modified after creation."""
        doc = ProcessedDocument(
            metadata=DocumentMetadata(
                title=None, author=None, subject=None,
                creator=None, producer=None, page_count=0,
            )
        )
        with pytest.raises(AttributeError):
            doc.metadata = DocumentMetadata(  # type: ignore[misc]
                title="X", author=None, subject=None,
                creator=None, producer=None, page_count=0,
            )
