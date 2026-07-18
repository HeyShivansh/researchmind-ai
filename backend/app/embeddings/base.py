"""Base embedding provider interface for the ResearchMind AI platform.

All embedding provider implementations should inherit from
``BaseEmbeddingProvider`` and implement the ``embed_text`` and
``embed_batch`` methods.  This allows new embedding backends
(Google Gemini, BAAI, Ollama, OpenAI, etc.) to be added without
modifying existing service or application code.

Each provider is responsible for ensuring the returned embedding
vectors have the correct dimension — the service layer does **not**
duplicate this validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import EmbeddingResult


class BaseEmbeddingProvider(ABC):
    """Abstract base class for all embedding providers.

    Subclasses must implement:

    - ``embed_text(text)`` — embed a single string.
    - ``embed_batch(texts)`` — embed a batch of strings.

    Subclasses must also expose the following properties for
    introspection and metadata propagation:

    - ``model_name`` — the identifier of the embedding model.
    - ``embedding_dimension`` — the dimensionality of produced vectors.

    Provider-specific logic (API keys, endpoints, authentication,
    dimension validation) should be handled in the subclass and never
    leak into the service layer.
    """

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    @abstractmethod
    def embed_text(self, text: str) -> EmbeddingResult:
        """Embed a single text string and return the result.

        The provider is responsible for validating the returned vector
        dimension and raising ``EmbeddingDimensionError`` if the
        dimension is unexpected.

        Parameters
        ----------
        text : str
            The input text to embed.  Must be non-empty.

        Returns
        -------
        EmbeddingResult
            An immutable result containing the vector, model name,
            and dimension.

        Raises
        ------
        EmptyEmbeddingError
            If *text* is empty.
        EmbeddingProviderError
            If the underlying provider call fails.
        EmbeddingDimensionError
            If the returned vector dimension does not match the
            provider's expected ``embedding_dimension``.
        """
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed a batch of texts and return results in the same order.

        The provider is responsible for validating that all returned
        vectors have consistent dimensions and matching what the
        provider expects.

        Parameters
        ----------
        texts : list[str]
            List of input texts to embed.  Each must be non-empty.

        Returns
        -------
        list[EmbeddingResult]
            One result per input text, in the same order.

        Raises
        ------
        EmptyEmbeddingError
            If *texts* is empty or any item is empty.
        EmbeddingProviderError
            If the underlying provider call fails.
        EmbeddingDimensionError
            If any returned vector dimension does not match the
            provider's expected ``embedding_dimension``.
        """
        ...

    # ------------------------------------------------------------------
    # Abstract properties
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the identifier of the embedding model."""
        ...

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimensionality of vectors produced by this provider."""
        ...
