"""Route package for the ResearchMind AI API."""

from .health import router as health_router
from .papers import router as paper_router

__all__ = [
    "health_router",
    "paper_router",
]
