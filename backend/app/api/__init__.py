"""API layer for the ResearchMind AI platform."""

from .routes import auth_router, health_router, paper_router, search_router

__all__ = [
    "auth_router",
    "health_router",
    "paper_router",
    "search_router",
]
