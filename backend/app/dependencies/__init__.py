"""Dependency injection package for the ResearchMind AI platform."""

from .database import get_db
from .services import get_paper_service

__all__ = [
    "get_db",
    "get_paper_service",
]
