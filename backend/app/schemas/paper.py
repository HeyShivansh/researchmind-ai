"""
Pydantic schemas for the Paper entity.

Defines request/response models used by the Paper API layer
following Pydantic v2 conventions.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaperBase(BaseModel):
    """
    Base schema with fields common to all Paper models.

    Attributes
    ----------
    title : str
        Title of the scientific paper.
    abstract : str | None
        Abstract or summary of the paper.
    doi : str | None
        Digital Object Identifier (unique per paper when available).
    publication_year : int | None
        Year the paper was published.
    pdf_path : str
        Filesystem path to the uploaded PDF file.
    """

    title: str = Field(
        ...,
        max_length=500,
        description="Title of the scientific paper",
    )
    abstract: str | None = Field(
        default=None,
        description="Abstract or summary of the paper",
    )
    doi: str | None = Field(
        default=None,
        max_length=255,
        description="Digital Object Identifier",
    )
    publication_year: int | None = Field(
        default=None,
        ge=1900,
        description="Year the paper was published",
    )
    pdf_path: str = Field(
        ...,
        max_length=1000,
        description="Filesystem path to the uploaded PDF",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("publication_year")
    @classmethod
    def validate_publication_year(
        cls, v: int | None
    ) -> int | None:
        """Ensure the publication year does not exceed the next year."""
        if v is not None and v > datetime.now().year + 1:
            raise ValueError(
                f"publication_year must not exceed {datetime.now().year + 1}"
            )
        return v


class PaperCreate(PaperBase):
    """
    Schema for creating a new paper.

    Inherits all fields from ``PaperBase`` without additions.
    """


# ------------------------------------------------------------------
# Update schema placeholder
#
# PaperUpdate will be added here when the update endpoint is
# designed.  Placing it in this location keeps CRUD schemas
# grouped together without future refactoring.
# ------------------------------------------------------------------


class PaperResponse(PaperBase):
    """
    Schema for returning a paper in API responses.

    Includes server-generated fields that are read-only at the
    API level.

    Attributes
    ----------
    id : UUID
        Unique identifier assigned by the database.
    filename : str or None
        Original uploaded filename.
    file_size : int or None
        File size in bytes.
    page_count : int or None
        Number of pages in the PDF.
    chunk_count : int or None
        Number of text chunks extracted.
    status : str
        Processing status ("processing", "ready", "error").
    author : str or None
        Author name extracted from PDF metadata.
    subject : str or None
        Subject extracted from PDF metadata.
    created_at : datetime
        Timestamp of when the record was created.
    updated_at : datetime
        Timestamp of the most recent update to the record.
    """

    id: UUID
    filename: str | None
    file_size: int | None
    page_count: int | None
    chunk_count: int | None
    status: str
    author: str | None
    subject: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
