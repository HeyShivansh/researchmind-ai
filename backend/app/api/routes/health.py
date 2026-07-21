import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.repositories.paper_repository import PaperRepository
from app.repositories.chunk_repository import ChunkRepository

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):

    # Check database connectivity
    db_status = "online"
    db_latency = None
    try:
        start = time.time()
        db.execute(text("SELECT 1"))
        db_latency = f"{int((time.time() - start) * 1000)}ms"
    except Exception:
        db_status = "offline"

    return {
        "status": "healthy" if db_status == "online" else "degraded",
        "database": db_status,
        "database_latency": db_latency,
    }


@router.get("/version")
def version():

    return {
        "version": "1.0.0"
    }


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """
    Readiness probe — indicates whether the application is fully initialized
    and ready to accept traffic. Unlike /health (which is a liveness check),
    this endpoint verifies that all dependencies are reachable and the
    application is in a functional state.
    """
    # Check database connectivity
    db_ready = False
    db_latency = None
    try:
        start = time.time()
        db.execute(text("SELECT 1"))
        db_latency = f"{int((time.time() - start) * 1000)}ms"
        db_ready = True
    except Exception:
        db_ready = False

    if not db_ready:
        raise HTTPException(status_code=503, detail="Database not ready")

    return {
        "status": "ready",
        "database": "connected",
        "database_latency": db_latency,
    }


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """
    Return application statistics for the dashboard.
    """
    paper_repo = PaperRepository(db)
    chunk_repo = ChunkRepository(db)

    total_papers = paper_repo.count()
    total_chunks = chunk_repo.count()
    papers = paper_repo.list(limit=10000)
    papers_processed = sum(1 for p in papers if p.status == "ready")
    papers_processing = sum(1 for p in papers if p.status == "processing")

    return {
        "total_papers": total_papers,
        "total_chunks": total_chunks,
        "papers_processed": papers_processed,
        "papers_processing": papers_processing,
    }