"""BAAI (BAAI/bge) embedding provider (placeholder).

This module will implement the ``BaseEmbeddingProvider`` interface for
BAAI's BGE (BAAI General Embedding) models, which are popular
open-source embedding models available via Hugging Face or the BAAI
Inference API.

Implementation steps (when ready):
1. Add a ``sentence-transformers`` or ``transformers`` dependency.
2. Load the model (e.g. ``BAAI/bge-small-en-v1.5``) on init.
3. Implement ``embed_text`` and ``embed_batch`` by running inference.
"""

from app.embeddings.base import BaseEmbeddingProvider
from app.embeddings.exceptions import EmbeddingProviderError
from app.embeddings.models import EmbeddingResult


class BAAIEmbeddingProvider(BaseEmbeddingProvider):
    """Placeholder for a BAAI BGE embedding provider.

    Raises ``EmbeddingProviderError`` on any call until implemented.
    """

    def __init__(self) -> None:
        self._model = "NOT_IMPLEMENTED"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def embedding_dimension(self) -> int:
        msg = "BAAIEmbeddingProvider is not yet implemented."
        raise EmbeddingProviderError(msg)

    def embed_text(self, text: str) -> EmbeddingResult:
        msg = "BAAIEmbeddingProvider is not yet implemented."
        raise EmbeddingProviderError(msg)

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        msg = "BAAIEmbeddingProvider is not yet implemented."
        raise EmbeddingProviderError(msg)
