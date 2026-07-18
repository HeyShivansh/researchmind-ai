"""Embedding orchestration service.

The ``EmbeddingService`` sits between application code and the
embedding provider.  It validates input, delegates to the provider,
and returns results.  Dimension validation is the provider's
responsibility — the service does not duplicate it.

No persistence or vector-database interaction happens here — the
service purely embeds text and returns ``EmbeddingResult`` objects.
"""

from __future__ import annotations

from .base import BaseEmbeddingProvider
from .exceptions import BatchEmbeddingError, EmptyEmbeddingError
from .models import EmbeddingResult


class EmbeddingService:
    """Orchestrates embedding requests through a configured provider.

    The service is provider-agnostic: it receives a
    ``BaseEmbeddingProvider`` via dependency injection and delegates
    all actual embedding work to that provider.

    Parameters
    ----------
    provider : BaseEmbeddingProvider
        The embedding provider to delegate to.
    batch_size : int or None
        Optional hint for future batch-splitting behaviour.
        Stored but not yet used for splitting.

    Examples
    --------
    >>> service = EmbeddingService(provider=some_provider)
    >>> result = service.embed_text("Hello, world!")
    >>> result.dimension
    768
    """

    def __init__(
        self,
        provider: BaseEmbeddingProvider,
        batch_size: int | None = None,
    ) -> None:
        self._provider = provider
        self._batch_size = batch_size

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def provider(self) -> BaseEmbeddingProvider:
        """Return the underlying embedding provider instance."""
        return self._provider

    @property
    def batch_size(self) -> int | None:
        """Return the configured batch size hint, if any."""
        return self._batch_size

    def embed_text(self, text: str) -> EmbeddingResult:
        """Embed a single text string.

        Parameters
        ----------
        text : str
            The input text to embed.  Must be non-empty.

        Returns
        -------
        EmbeddingResult
            The embedding result with vector, model name, and dimension.

        Raises
        ------
        EmptyEmbeddingError
            If *text* is empty.
        EmbeddingProviderError
            If the provider call fails.
        """
        self._validate_text(text)
        return self._provider.embed_text(text)

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed a batch of texts.

        All items are processed through the provider in a single call
        when the provider supports it.  Results are returned in the
        same order as the input texts.

        Parameters
        ----------
        texts : list[str]
            List of input texts to embed.  Must not be empty.

        Returns
        -------
        list[EmbeddingResult]
            One result per input text, preserving order.

        Raises
        ------
        EmptyEmbeddingError
            If *texts* is empty or any individual item is empty.
        EmbeddingProviderError
            If the provider call fails.
        BatchEmbeddingError
            If the number of results does not match the number of
            inputs (indicating a partial failure).
        """
        self._validate_batch(texts)
        results = self._provider.embed_batch(texts)
        self._validate_batch_results(texts, results)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_text(text: str) -> None:
        """Raise ``EmptyEmbeddingError`` if *text* is empty or blank."""
        if not text or not text.strip():
            raise EmptyEmbeddingError(
                "Cannot embed empty or whitespace-only text."
            )

    def _validate_batch(self, texts: list[str]) -> None:
        """Validate the batch input before calling the provider."""
        if not texts:
            raise EmptyEmbeddingError("Cannot embed an empty batch.")

        failed: list[int] = []
        for i, t in enumerate(texts):
            if not t or not t.strip():
                failed.append(i)

        if failed:
            raise EmptyEmbeddingError(
                f"Batch contains empty items at indices: {failed}"
            )

    @staticmethod
    def _validate_batch_results(
        texts: list[str],
        results: list[EmbeddingResult],
    ) -> None:
        """Verify the number of results matches the number of inputs."""
        if len(results) != len(texts):
            raise BatchEmbeddingError(
                f"Expected {len(texts)} results but provider returned "
                f"{len(results)}.",
                failed_indices=list(range(len(results), len(texts))),
            )
