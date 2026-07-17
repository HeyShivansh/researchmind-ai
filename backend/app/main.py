"""Application entrypoint for the ResearchMind AI platform."""

from fastapi import FastAPI

from app.api import health_router, paper_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(health_router)
app.include_router(paper_router)

register_exception_handlers(app)


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple health-check payload for the API root."""
    return {
        "message": "ResearchMind AI API",
        "status": "running",
    }