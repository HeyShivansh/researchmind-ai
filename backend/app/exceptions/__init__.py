"""Domain exceptions for the ResearchMind AI platform."""

from .paper import (
    DuplicatePaperError,
    PaperError,
    PaperNotFoundError,
)

__all__ = [
    "PaperError",
    "PaperNotFoundError",
    "DuplicatePaperError",
]
