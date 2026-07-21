"""Data models for the embedding subsystem.

Uses ``dataclasses`` for lightweight, immutable, typed structures
that represent the output of the embedding layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingResult:
    """The result of embedding a single text string.

    The original input text is **not** stored — the caller already
    knows which text was embedded.

    Attributes
    ----------
    vector : list[float]
        The embedding vector as a list of floats.
    model_name : str
        Name of the embedding model that produced this vector.
    dimension : int
        The dimensionality of the embedding vector.
        Must equal ``len(vector)``.

    Examples
    --------
    >>> result = EmbeddingResult(
    ...     vector=[0.1, 0.2, 0.3],
    ...     model_name="gemini-embedding-001",
    ...     dimension=3,
    ... )
    >>> result.dimension
    3
    """

    vector: list[float]
    model_name: str
    dimension: int
