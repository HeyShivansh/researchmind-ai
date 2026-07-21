"""Google Gemini embedding provider.

Uses the Gemini Embedding API to produce text embeddings.  The
provider communicates via the ``google-genai`` SDK or, if
unavailable, falls back to direct HTTP requests using ``httpx``.

The embedding dimension is **not** hardcoded — it is discovered
from the first API response and cached for subsequent calls.
An optional ``output_dimensionality`` parameter can be set to
truncate embeddings to a smaller size (e.g. 768) via Matryoshka
Representation Learning (MRL).
"""

from __future__ import annotations

from app.embeddings.base import BaseEmbeddingProvider
from app.embeddings.exceptions import (
    EmbeddingDimensionError,
    EmbeddingProviderError,
)
from app.embeddings.models import EmbeddingResult

# ---------------------------------------------------------------------------
# Default model constant
# ---------------------------------------------------------------------------

DEFAULT_MODEL: str = "gemini-embedding-001"


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider backed by Google's Gemini Embedding API.

    The embedding dimension is discovered from the first API response
    rather than assumed.  This makes the provider resilient to model
    changes that affect output dimensionality.

    Parameters
    ----------
    api_key : str
        Google Generative AI API key.
    model : str
        The Gemini embedding model name.
        Defaults to ``gemini-embedding-001``.
    output_dimensionality : int or None
        Desired output vector dimension via MRL truncation.
        Set to ``None`` to use the model's default (3072).
        Defaults to 768 to match the application's Qdrant
        vector dimension.

    Examples
    --------
    >>> provider = GeminiEmbeddingProvider(api_key="...")
    >>> result = provider.embed_text("What is the capital of France?")
    >>> result.dimension
    768
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        output_dimensionality: int | None = 768,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._output_dim = output_dimensionality
        # Dimension is discovered lazily from the first API response.
        self._dimension: int | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def model_name(self) -> str:
        """Return the configured Gemini embedding model identifier."""
        return self._model

    @property
    def embedding_dimension(self) -> int:
        """Return the discovered dimensionality.

        Raises
        ------
        RuntimeError
            If no embedding has been computed yet.
        """
        if self._dimension is None:
            raise RuntimeError(
                "GeminiEmbeddingProvider: dimension unknown until the "
                "first successful embedding call."
            )
        return self._dimension

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> EmbeddingResult:
        """Embed a single text string via the Gemini Embedding API.

        Parameters
        ----------
        text : str
            The input text to embed.  Must be non-empty.

        Returns
        -------
        EmbeddingResult
            An immutable result containing the vector and metadata.
            The dimension is derived from the actual vector length.

        Raises
        ------
        EmbeddingProviderError
            If the API call fails or the response is malformed.
        """
        vector = self._call_api(text)
        self._cache_dimension(vector)
        return EmbeddingResult(
            vector=vector,
            model_name=self._model,
            dimension=len(vector),
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Embed a batch of texts via the Gemini Embedding API.

        Parameters
        ----------
        texts : list[str]
            List of input texts to embed.

        Returns
        -------
        list[EmbeddingResult]
            One result per input text, in the same order.
            The dimension is derived from the actual vector length.

        Raises
        ------
        EmbeddingProviderError
            If the API call fails or the response is malformed.
        EmbeddingDimensionError
            If vectors within the batch have inconsistent dimensions.
        """
        vectors = self._call_api_batch(texts)
        self._validate_consistent_dimensions(vectors)
        self._cache_dimension(vectors[0])
        return [
            EmbeddingResult(
                vector=v,
                model_name=self._model,
                dimension=len(v),
            )
            for v in vectors
        ]

    # ------------------------------------------------------------------
    # Internal API helpers
    # ------------------------------------------------------------------

    def _call_api(self, text: str) -> list[float]:
        """Call the Gemini embedding API for a single text.

        Attempts to use the ``google-genai`` SDK first, then
        falls back to a direct HTTP request via ``httpx``.

        Parameters
        ----------
        text : str
            The text to embed.

        Returns
        -------
        list[float]
            The embedding vector.

        Raises
        ------
        EmbeddingProviderError
            If the API call fails.
        """
        try:
            return self._call_api_sdk(text)
        except ImportError:
            return self._call_api_http(text)

    def _call_api_batch(self, texts: list[str]) -> list[list[float]]:
        """Call the Gemini embedding API for a batch of texts.

        Parameters
        ----------
        texts : list[str]
            The texts to embed.

        Returns
        -------
        list[list[float]]
            One embedding vector per input text.

        Raises
        ------
        EmbeddingProviderError
            If the API call fails.
        """
        try:
            return self._call_api_batch_sdk(texts)
        except ImportError:
            return self._call_api_batch_http(texts)

    # ------------------------------------------------------------------
    # SDK-based calls (preferred — google-genai)
    # ------------------------------------------------------------------

    def _call_api_sdk(self, text: str) -> list[float]:
        """Embed via the ``google-genai`` SDK.

        Uses ``client.models.embed_content`` with the new
        ``google.genai`` client library.
        """
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types as genai_types  # type: ignore[import-untyped]

        client = genai.Client(api_key=self._api_key)
        config = (
            genai_types.EmbedContentConfig(
                output_dimensionality=self._output_dim,
            )
            if self._output_dim is not None
            else None
        )
        result = client.models.embed_content(
            model=self._model,
            contents=text,
            config=config,
        )
        return list(result.embeddings[0].values)

    def _call_api_batch_sdk(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed via the ``google-genai`` SDK."""
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types as genai_types  # type: ignore[import-untyped]

        client = genai.Client(api_key=self._api_key)
        config = (
            genai_types.EmbedContentConfig(
                output_dimensionality=self._output_dim,
            )
            if self._output_dim is not None
            else None
        )
        result = client.models.embed_content(
            model=self._model,
            contents=texts,
            config=config,
        )
        return [list(emb.values) for emb in result.embeddings]

    # ------------------------------------------------------------------
    # HTTP fallback calls
    # ------------------------------------------------------------------

    def _call_api_http(self, text: str) -> list[float]:
        """Embed via a direct HTTP request to the Gemini API."""
        import httpx

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:embedContent?key={self._api_key}"
        )
        payload: dict = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
        }
        if self._output_dim is not None:
            payload["output_dimensionality"] = self._output_dim

        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.post(url, json=payload)

        if response.status_code != 200:
            raise EmbeddingProviderError(
                f"Gemini API returned status {response.status_code}: "
                f"{response.text}",
                provider_name="gemini",
            )

        data = response.json()
        return list(data["embedding"]["values"])

    def _call_api_batch_http(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed via a direct HTTP request to the Gemini API."""
        import httpx

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:batchEmbedContents?key={self._api_key}"
        )
        requests = []
        for t in texts:
            req: dict = {
                "model": f"models/{self._model}",
                "content": {"parts": [{"text": t}]},
            }
            if self._output_dim is not None:
                req["output_dimensionality"] = self._output_dim
            requests.append(req)

        payload = {"requests": requests}

        with httpx.Client(timeout=60.0) as http_client:
            response = http_client.post(url, json=payload)

        if response.status_code != 200:
            raise EmbeddingProviderError(
                f"Gemini API returned status {response.status_code}: "
                f"{response.text}",
                provider_name="gemini",
            )

        data = response.json()
        return [
            list(emb["values"])
            for emb in data.get("embeddings", [])
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cache_dimension(self, vector: list[float]) -> None:
        """Cache the vector dimension if not already known.

        If the dimension was already cached and differs, raise an
        error — this indicates an unexpected model change.
        """
        dim = len(vector)
        if self._dimension is None:
            self._dimension = dim
        elif self._dimension != dim:
            raise EmbeddingDimensionError(
                f"Gemini model '{self._model}' returned a vector of "
                f"dimension {dim}, but expected {self._dimension} "
                f"(from previous calls).",
                expected=self._dimension,
                actual=dim,
            )

    @staticmethod
    def _validate_consistent_dimensions(vectors: list[list[float]]) -> None:
        """Verify all vectors in a batch have the same dimension."""
        if not vectors:
            return
        first = len(vectors[0])
        for i, v in enumerate(vectors[1:], start=1):
            if len(v) != first:
                raise EmbeddingDimensionError(
                    f"Batch item {i} has dimension {len(v)}, "
                    f"but expected {first} (from item 0).",
                    expected=first,
                    actual=len(v),
                )
