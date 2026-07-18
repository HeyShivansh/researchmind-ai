"""Domain exceptions for the embedding subsystem.

Exception hierarchy::

    EmbeddingError
    ├── EmbeddingProviderError
    ├── EmbeddingDimensionError
    ├── EmptyEmbeddingError
    └── BatchEmbeddingError
"""


class EmbeddingError(Exception):
    """Base exception for all embedding-related errors.

    All custom embedding exceptions inherit from this class so callers
    can catch a single base type when they don't need granularity.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmbeddingProviderError(EmbeddingError):
    """Raised when the underlying embedding provider fails.

    This covers network errors, API timeouts, authentication failures,
    and malformed responses from the provider.
    """

    def __init__(self, message: str, *, provider_name: str | None = None) -> None:
        self.provider_name = provider_name
        super().__init__(message)


class EmbeddingDimensionError(EmbeddingError):
    """Raised when a returned embedding vector has an unexpected dimension.

    This can occur when:
    - The provider model changed between calls.
    - The provider returned a malformed response.
    - The service is configured with an incorrect expected dimension.
    """

    def __init__(
        self,
        message: str,
        *,
        expected: int | None = None,
        actual: int | None = None,
    ) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(message)


class EmptyEmbeddingError(EmbeddingError):
    """Raised when empty input text is provided for embedding.

    Providers typically cannot embed empty strings, so this error
    allows the service to fail fast with a clear message before
    making an API call.
    """

    def __init__(self, message: str = "Cannot embed empty text.") -> None:
        super().__init__(message)


class BatchEmbeddingError(EmbeddingError):
    """Raised when one or more items in a batch embedding fail.

    Tracks the indices of failed items so callers can retry or
    report partial failures.

    Attributes
    ----------
    failed_indices : list[int]
        0-based indices of the items that failed to embed.
    """

    def __init__(
        self,
        message: str,
        *,
        failed_indices: list[int] | None = None,
    ) -> None:
        self.failed_indices = failed_indices or []
        super().__init__(message)
