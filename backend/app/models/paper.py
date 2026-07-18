"""
Paper ORM model for the ResearchMind AI platform.

Represents a scientific paper stored in the PostgreSQL database.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Paper(Base):
    """
    A scientific paper.

    Stores bibliographic metadata and the path to the uploaded PDF file.
    Each paper is uniquely identified by its DOI when available.
    """

    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        index=True,
        nullable=False,
    )
    abstract: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    doi: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
    )
    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    pdf_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # -- Relationship to chunks ----------------------------------------------
    chunks: Mapped[list["PaperChunk"]] = relationship(
        "PaperChunk",
        back_populates="paper",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f'Paper(title="{self.title}")'
