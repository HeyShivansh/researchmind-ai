"""
Search API router.

Provides hybrid retrieval endpoints that combine semantic search
(Qdrant) and BM25 keyword search using Reciprocal Rank Fusion.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_hybrid_retrieval_service
from app.hybrid import HybridRetrievalService
from app.models.paper import Paper
from app.retrieval.models import RetrievedChunk

router = APIRouter(prefix="/search", tags=["search"])


def _resolve_paper_titles(
    results: list[RetrievedChunk],
    db: Session,
) -> dict[UUID, str]:
    """
    Resolve paper titles for a list of retrieved chunks.

    Performs a single batch query to fetch all distinct paper IDs,
    then maps each chunk to its paper title.
    """
    paper_ids = {r.paper_id for r in results}
    if not paper_ids:
        return {}

    from sqlalchemy import select

    stmt = select(Paper.id, Paper.title).where(Paper.id.in_(paper_ids))
    rows = db.execute(stmt).all()
    return {row.id: row.title for row in rows}


@router.post("/")
def search(
    query: str,
    top_k: int = 10,
    mode: str = "hybrid",
    hybrid_service: HybridRetrievalService = Depends(get_hybrid_retrieval_service),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Search across all indexed papers.

    Supports three retrieval modes:
    - ``hybrid`` (default): semantic + BM25 with RRF fusion
    - ``semantic``: vector similarity search only
    - ``keyword``: BM25 keyword search only

    Parameters
    ----------
    query : str
        The search query text.
    top_k : int
        Number of results to return. Defaults to 10.
    mode : str
        Retrieval mode. One of "hybrid", "semantic", or "keyword".

    Returns
    -------
    dict
        Results with the search response including results list,
        total count, and query metadata.
    """
    start = time.time()

    mode = mode.lower()
    if mode not in ("hybrid", "semantic", "keyword"):
        mode = "hybrid"

    if mode == "semantic":
        results: list[RetrievedChunk] = hybrid_service.semantic_search(query, top_k=top_k)
    elif mode == "keyword":
        results = hybrid_service.keyword_search(query, top_k=top_k)
    else:
        results = hybrid_service.hybrid_search(query, top_k=top_k)

    # Resolve paper titles for all results in a single query
    paper_titles = _resolve_paper_titles(results, db)

    elapsed_ms = int((time.time() - start) * 1000)

    return {
        "results": [
            {
                "chunk_id": str(r.chunk_id),
                "paper_id": str(r.paper_id),
                "paper_title": paper_titles.get(r.paper_id, ""),
                "text": r.text,
                "page_number": r.page_number,
                "chunk_index": r.chunk_index,
                "score": r.score,
                "source": mode,
            }
            for r in results
        ],
        "total_results": len(results),
        "query": query,
        "took_ms": elapsed_ms,
    }
