"""
Base chunker interface for the ResearchMind AI platform.

All chunker implementations should inherit from ``BaseChunker`` and
implement the ``chunk`` method.  This allows new chunking strategies
(semantic, markdown, scientific, section-aware) to be added without
modifying existing code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.processing.models import ProcessedDocument

from .models import DocumentChunk


class BaseChunker(ABC):
    """
    Abstract base class for all chunking strategies.

    Subclasses must implement ``chunk()`` which takes a
    ``ProcessedDocument`` and returns a list of ``DocumentChunk``
    objects.
    """

    @abstractmethod
    def chunk(self, document: ProcessedDocument) -> list[DocumentChunk]:
        """
        Split a processed document into chunks.

        Parameters
        ----------
        document : ProcessedDocument
            The processed PDF document to chunk.

        Returns
        -------
        list[DocumentChunk]
            Ordered list of chunks spanning the entire document.
        """
        ...
