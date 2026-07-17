"""API layer for the ResearchMind AI platform."""

from .routes import health_router, paper_router

__all__ = [
    "health_router",
    "paper_router",
]
