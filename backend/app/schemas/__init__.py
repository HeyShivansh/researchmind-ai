"""
Pydantic schemas for the ResearchMind AI platform.
"""

from .paper import (
    PaperBase,
    PaperCreate,
    PaperResponse,
)

__all__ = [
    "PaperBase",
    "PaperCreate",
    "PaperResponse",
]
