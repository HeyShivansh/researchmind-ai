"""
Paper API router.

Defines the HTTP endpoints for the Paper resource.  Each endpoint
delegates to the service layer and returns Pydantic response models.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

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
