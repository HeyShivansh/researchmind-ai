"""
Paper API router.

Defines the HTTP endpoints for the Paper resource.  Each endpoint
delegates to the service layer and returns Pydantic response models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.dependencies import get_paper_service
from app.models.paper import Paper
from app.schemas.paper import PaperCreate, PaperResponse
from app.services.paper_service import PaperService

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post(
    "/",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper(
    paper: PaperCreate,
    service: PaperService = Depends(get_paper_service),
) -> Paper:
    """
    Create a new paper.

    If the paper includes a DOI, the endpoint ensures no duplicate
    DOI exists before persisting the record.
    """
    return service.create_paper(paper)


@router.get(
    "/",
    response_model=list[PaperResponse],
)
def list_papers(
    skip: int = 0,
    limit: int = 100,
    service: PaperService = Depends(get_paper_service),
) -> list[Paper]:
    """
    Retrieve a paginated list of all papers.
    """
    return service.list_papers(skip=skip, limit=limit)


@router.get(
    "/{paper_id}",
    response_model=PaperResponse,
)
def get_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service),
) -> Paper:
    """
    Retrieve a single paper by its unique identifier.
    """
    return service.get_paper(paper_id)


@router.delete(
    "/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service),
) -> None:
    """
    Delete a paper and all associated data.

    Removes the paper record, its chunks from PostgreSQL, vectors
    from Qdrant, and the PDF file from storage.
    """
    service.delete_paper(paper_id)


@router.get(
    "/{paper_id}/chunks",
    response_model=list[dict[str, Any]],
)
def get_paper_chunks(
    paper_id: UUID,
    skip: int = 0,
    limit: int = 1000,
    service: PaperService = Depends(get_paper_service),
) -> list[dict[str, Any]]:
    """
    Retrieve chunks for a paper, ordered by chunk index.

    Returns basic chunk information including id, paper_id, text,
    page_number, and chunk_index.
    """
    chunks = service.get_paper_chunks(paper_id, skip=skip, limit=limit)
    return [
        {
            "id": str(chunk.id),
            "paper_id": str(chunk.paper_id),
            "text": chunk.text,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "char_count": chunk.char_count,
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
        }
        for chunk in chunks
    ]


@router.get(
    "/{paper_id}/file",
    response_class=FileResponse,
)
def get_paper_file(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service),
) -> FileResponse:
    """
    Serve the uploaded PDF file for a paper.

    Returns the file inline (``Content-Disposition: inline``) so that
    the browser's PDF viewer can display it directly rather than forcing
    a download. The original upload filename is passed for display.
    """
    paper = service.get_paper(paper_id)

    # Resolve the file path using the same FileStorage as the upload pipeline
    pdf_path = Path(paper.pdf_path)
    if not pdf_path.is_absolute():
        from app.core.config import settings
        from app.storage.file_storage import FileStorage

        storage = FileStorage(settings)
        pdf_path = storage.root / paper.pdf_path

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file not found for paper {paper_id}",
        )

    # Use the original filename for the response, falling back to paper_id-based name
    display_filename = paper.filename or f"{paper_id}.pdf"

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=display_filename,
        content_disposition_type="inline",
    )


@router.post(
    "/upload",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_paper(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str | None = Form(default=None, description="Paper title"),
    doi: str | None = Form(default=None, description="Digital Object Identifier"),
    publication_year: int | None = Form(default=None, description="Year of publication"),
    abstract: str | None = Form(default=None, description="Paper abstract"),
    service: PaperService = Depends(get_paper_service),
) -> Paper:
    """
    Upload a PDF and create a Paper record.

    The file is validated (extension, magic bytes, size), saved to
    the storage layer, and a database record is created.  If either
    step fails the operation is rolled back atomically.
    """
    file_bytes = await file.read()
    return service.upload_paper(
        file_bytes,
        file.filename or "upload.pdf",
        title=title,
        doi=doi,
        publication_year=publication_year,
        abstract=abstract,
    )
