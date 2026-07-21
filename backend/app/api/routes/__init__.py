"""Route package for the ResearchMind AI API."""

from .auth import router as auth_router
from .health import router as health_router
from .papers import router as paper_router
from .search import router as search_router

__all__ = [
    "auth_router",
    "health_router",
    "paper_router",
    "search_router",
]
