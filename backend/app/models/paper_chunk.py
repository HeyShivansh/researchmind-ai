"""
PaperChunk ORM model for the ResearchMind AI platform.

Represents a single chunk of text extracted from a paper's PDF,
persisted in PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PaperChunk(Base):
    """
    A single chunk of text from a paper's PDF.

    Each chunk stores the extracted text along with positional metadata
    so that the original document can be partially reconstructed or
    displayed with page/chunk annotations.

    Attributes
    ----------
    id : UUID
        Unique identifier for this chunk.
    paper_id : UUID
        Foreign key referencing the parent ``Paper``.
    page_number : int
        1-based page number from the source PDF.
    chunk_index : int
        Global index of this chunk across the entire document (0-based).
    text : str
        The chunk content.
    char_start : int
        Starting character offset within the original page text.
    char_end : int
        Ending character offset (exclusive) within the original page text.
    char_count : int
        Number of characters in this chunk's text.
    created_at : datetime
        Timestamp of when the record was created.
    """

    __tablename__ = "paper_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    char_start: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    char_end: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    # -- Relationship back to Paper -----------------------------------------
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return (
            f"PaperChunk(id={self.id}, paper_id={self.paper_id}, "
            f"page={self.page_number}, chunk_index={self.chunk_index})"
        )
