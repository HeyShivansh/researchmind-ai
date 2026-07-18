"""Ollama embedding provider (placeholder).

This module will implement the ``BaseEmbeddingProvider`` interface for
locally-hosted embedding models served via Ollama (e.g. ``nomic-embed-text``,
``all-minilm``).

Ollama exposes a simple REST API at ``http://localhost:11434/api/embeddings``.

Implementation steps (when ready):
1. Configure the Ollama endpoint URL.
2. Implement ``embed_text`` by POSTing to the Ollama API.
3. Implement ``embed_batch`` by iterating or using the batch endpoint.
"""

from app.embeddings.base import BaseEmbeddingProvider
from app.embeddings.exceptions import EmbeddingProviderError
from app.embeddings.models import EmbeddingResult


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Placeholder for an Ollama-backed embedding provider.

    Raises ``EmbeddingProviderError`` on any call until implemented.
    """

    def __init__(self) -> None:
        self._model = "NOT_IMPLEMENTED"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def embedding_dimension(self) -> int:
        msg = "OllamaEmbeddingProvider is not yet implemented."
        raise EmbeddingProviderError(msg)

    def embed_text(self, text: str) -> EmbeddingResult:
        msg = "OllamaEmbeddingProvider is not yet implemented."
        raise EmbeddingProviderError(msg)

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        msg = "OllamaEmbeddingProvider is not yet implemented."
        raise EmbeddingProviderError(msg)
