"""Unit tests for the embedding subsystem.

Tests cover BaseEmbeddingProvider, EmbeddingResult, EmbeddingService,
and exceptions.  All external providers are mocked — no real API calls
are made.  No database or FastAPI dependencies.

Run with::

    uv run pytest tests/test_embeddings.py -v
"""

from __future__ import annotations

import pytest

from app.embeddings import (
    BaseEmbeddingProvider,
    BatchEmbeddingError,
    EmbeddingDimensionError,
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingResult,
    EmbeddingService,
    EmptyEmbeddingError,
)


# ===================================================================
# EmbeddingResult model
# ===================================================================


class TestEmbeddingResult:
    """Tests for the ``EmbeddingResult`` dataclass."""

    def test_is_frozen(self) -> None:
        """Verify ``EmbeddingResult`` cannot be modified after creation."""
        result = EmbeddingResult(
            vector=[0.1, 0.2, 0.3],
            model_name="test-model",
            dimension=3,
        )
        with pytest.raises(AttributeError):
            result.vector = [9.9]  # type: ignore[misc]

    def test_fields_are_stored(self) -> None:
        """Verify all fields are stored as passed."""
        result = EmbeddingResult(
            vector=[0.5, -0.1, 0.8, 0.0],
            model_name="text-embedding-004",
            dimension=4,
        )
        assert result.vector == [0.5, -0.1, 0.8, 0.0]
        assert result.model_name == "text-embedding-004"
        assert result.dimension == 4

    def test_no_text_field(self) -> None:
        """Verify ``EmbeddingResult`` does **not** store the original text."""
        result = EmbeddingResult(
            vector=[0.1, 0.2, 0.3],
            model_name="m",
            dimension=3,
        )
        assert not hasattr(result, "text")


# ===================================================================
# BaseEmbeddingProvider interface
# ===================================================================


class TestBaseEmbeddingProvider:
    """Tests for the ``BaseEmbeddingProvider`` ABC."""

    def test_cannot_instantiate(self) -> None:
        """Verify ``BaseEmbeddingProvider`` cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseEmbeddingProvider()  # type: ignore[abstract]


# ===================================================================
# Fake provider for service tests
# ===================================================================


class FakeProvider(BaseEmbeddingProvider):
    """A fake provider that returns predictable embeddings.

    The provider owns dimension validation — it raises
    ``EmbeddingDimensionError`` when configured to return a
    wrong-dimension vector.
    """

    def __init__(
        self,
        *,
        model: str = "fake-model",
        dimension: int = 4,
        fail_on: str | None = None,
        return_wrong_dimension: bool = False,
    ) -> None:
        self._model = model
        self._dimension = dimension
        self._fail_on = fail_on
        self._return_wrong_dimension = return_wrong_dimension

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def embedding_dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> EmbeddingResult:
        if self._fail_on == "embed_text":
            raise EmbeddingProviderError("Provider failure", provider_name="fake")

        actual_dim = self._dimension if not self._return_wrong_dimension else self._dimension + 1

        if self._return_wrong_dimension:
            raise EmbeddingDimensionError(
                f"Expected dim {self._dimension}, got {actual_dim}",
                expected=self._dimension,
                actual=actual_dim,
            )

        return EmbeddingResult(
            vector=[0.1] * self._dimension,
            model_name=self._model,
            dimension=self._dimension,
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        if self._fail_on == "embed_batch":
            raise EmbeddingProviderError("Batch failure", provider_name="fake")

        actual_dim = self._dimension if not self._return_wrong_dimension else self._dimension + 1

        if self._return_wrong_dimension:
            raise EmbeddingDimensionError(
                f"Expected dim {self._dimension}, got {actual_dim}",
                expected=self._dimension,
                actual=actual_dim,
            )

        return [
            EmbeddingResult(
                vector=[0.2] * self._dimension,
                model_name=self._model,
                dimension=self._dimension,
            )
            for t in texts
        ]


class WrongCountProvider(FakeProvider):
    """Provider that returns fewer results than inputs (for testing)."""

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        # Return one fewer result than requested
        return [
            EmbeddingResult(
                vector=[0.1] * self._dimension,
                model_name=self._model,
                dimension=self._dimension,
            )
            for t in texts[:-1]
        ]


# ===================================================================
# EmbeddingService — single embedding
# ===================================================================


class TestEmbedText:
    """Tests for ``EmbeddingService.embed_text``."""

    def test_single_embedding(self) -> None:
        """Verify a single text produces a valid ``EmbeddingResult``."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        result = service.embed_text("Hello, world!")

        assert isinstance(result, EmbeddingResult)
        assert len(result.vector) == 4
        assert result.dimension == 4
        assert result.model_name == "fake-model"

    def test_empty_input_raises_error(self) -> None:
        """Verify empty text raises ``EmptyEmbeddingError``."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmptyEmbeddingError, match="empty"):
            service.embed_text("")

    def test_whitespace_only_raises_error(self) -> None:
        """Verify whitespace-only text raises ``EmptyEmbeddingError``."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmptyEmbeddingError, match="empty"):
            service.embed_text("   \t\n  ")

    def test_provider_failure_propagates(self) -> None:
        """Verify a provider failure raises ``EmbeddingProviderError``."""
        provider = FakeProvider(fail_on="embed_text")
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmbeddingProviderError, match="Provider failure"):
            service.embed_text("Hello")

    def test_dimension_error_from_provider_propagates(self) -> None:
        """Verify a provider's ``EmbeddingDimensionError`` passes through."""
        provider = FakeProvider(return_wrong_dimension=True)
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmbeddingDimensionError, match="Expected dim"):
            service.embed_text("Hello")


# ===================================================================
# EmbeddingService — batch embedding
# ===================================================================


class TestEmbedBatch:
    """Tests for ``EmbeddingService.embed_batch``."""

    def test_batch_embedding(self) -> None:
        """Verify a batch of texts returns results in order."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        texts = ["First text", "Second text", "Third text"]
        results = service.embed_batch(texts)

        assert len(results) == 3
        for result in results:
            assert len(result.vector) == 4
            assert result.dimension == 4

    def test_empty_batch_raises_error(self) -> None:
        """Verify an empty batch raises ``EmptyEmbeddingError``."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmptyEmbeddingError, match="empty batch"):
            service.embed_batch([])

    def test_batch_with_empty_item_raises_error(self) -> None:
        """Verify a batch containing an empty string raises ``EmptyEmbeddingError``."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmptyEmbeddingError, match="empty items"):
            service.embed_batch(["valid", "", "also valid"])

    def test_batch_provider_failure_propagates(self) -> None:
        """Verify provider failure during batch raises ``EmbeddingProviderError``."""
        provider = FakeProvider(fail_on="embed_batch")
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmbeddingProviderError, match="Batch failure"):
            service.embed_batch(["Hello", "World"])

    def test_batch_result_count_mismatch(self) -> None:
        """Verify mismatched result count raises ``BatchEmbeddingError``."""
        provider = WrongCountProvider()
        service = EmbeddingService(provider=provider)

        with pytest.raises(BatchEmbeddingError, match="Expected 3"):
            service.embed_batch(["A", "B", "C"])

    def test_batch_dimension_error_from_provider_propagates(self) -> None:
        """Verify a provider's dimension error passes through in batch mode."""
        provider = FakeProvider(return_wrong_dimension=True)
        service = EmbeddingService(provider=provider)

        with pytest.raises(EmbeddingDimensionError, match="Expected dim"):
            service.embed_batch(["Hello", "World"])


# ===================================================================
# EmbeddingService — metadata propagation
# ===================================================================


class TestMetadataPropagation:
    """Tests that metadata from providers propagates through the service."""

    def test_model_name_propagated(self) -> None:
        """Verify ``model_name`` from provider is preserved in results."""
        provider = FakeProvider(model="custom-embedding-model-v2")
        service = EmbeddingService(provider=provider)

        result = service.embed_text("Hello")

        assert result.model_name == "custom-embedding-model-v2"

    def test_dimension_propagated(self) -> None:
        """Verify ``dimension`` from provider is preserved in results."""
        provider = FakeProvider(dimension=768)
        service = EmbeddingService(provider=provider)

        result = service.embed_text("Hello")

        assert result.dimension == 768
        assert len(result.vector) == 768

    def test_batch_metadata_propagated(self) -> None:
        """Verify model info propagates through batch results."""
        provider = FakeProvider(model="batch-model", dimension=128)
        service = EmbeddingService(provider=provider)

        results = service.embed_batch(["A", "B"])

        for r in results:
            assert r.model_name == "batch-model"
            assert r.dimension == 128
            assert len(r.vector) == 128


# ===================================================================
# EmbeddingService — provider property
# ===================================================================


class TestProviderProperty:
    """Tests for the ``provider`` property on ``EmbeddingService``."""

    def test_provider_accessible(self) -> None:
        """Verify the injected provider is accessible via the property."""
        provider = FakeProvider()
        service = EmbeddingService(provider=provider)

        assert service.provider is provider


# ===================================================================
# EmbeddingService — batch_size configuration
# ===================================================================


class TestBatchSize:
    """Tests for the ``batch_size`` configuration on ``EmbeddingService``."""

    def test_default_is_none(self) -> None:
        """Verify default ``batch_size`` is ``None``."""
        service = EmbeddingService(provider=FakeProvider())
        assert service.batch_size is None

    def test_custom_batch_size(self) -> None:
        """Verify a custom ``batch_size`` is stored."""
        service = EmbeddingService(provider=FakeProvider(), batch_size=32)
        assert service.batch_size == 32

    def test_zero_batch_size(self) -> None:
        """Verify ``batch_size=0`` is accepted (no splitting yet)."""
        service = EmbeddingService(provider=FakeProvider(), batch_size=0)
        assert service.batch_size == 0


# ===================================================================
# Exception hierarchy
# ===================================================================


class TestExceptionHierarchy:
    """Tests for the embedding exception hierarchy."""

    def test_all_caught_by_base(self) -> None:
        """Verify all custom exceptions can be caught as ``EmbeddingError``."""
        exceptions: list[EmbeddingError] = [
            EmbeddingProviderError("msg"),
            EmbeddingDimensionError("msg"),
            EmptyEmbeddingError("msg"),
            BatchEmbeddingError("msg"),
        ]

        for exc in exceptions:
            assert isinstance(exc, EmbeddingError)
            assert isinstance(exc, Exception)

    def test_provider_error_has_name(self) -> None:
        """Verify ``EmbeddingProviderError`` stores the provider name."""
        exc = EmbeddingProviderError("fail", provider_name="gemini")
        assert exc.provider_name == "gemini"
        assert str(exc) == "fail"

    def test_dimension_error_has_expected_actual(self) -> None:
        """Verify ``EmbeddingDimensionError`` stores expected/actual values."""
        exc = EmbeddingDimensionError("mismatch", expected=768, actual=512)
        assert exc.expected == 768
        assert exc.actual == 512

    def test_batch_error_has_failed_indices(self) -> None:
        """Verify ``BatchEmbeddingError`` stores failed indices."""
        exc = BatchEmbeddingError("partial", failed_indices=[2, 3])
        assert exc.failed_indices == [2, 3]

    def test_empty_error_default_message(self) -> None:
        """Verify ``EmptyEmbeddingError`` has a sensible default message."""
        exc = EmptyEmbeddingError()
        assert "empty" in str(exc).lower()


# ===================================================================
# FakeProvider edge cases
# ===================================================================


class TestFakeProviderDirect:
    """Tests for the FakeProvider used in tests."""

    def test_direct_embed_text(self) -> None:
        """Verify the fake provider works standalone."""
        provider = FakeProvider()
        result = provider.embed_text("hello")
        assert len(result.vector) == 4

    def test_direct_embed_batch(self) -> None:
        """Verify the fake batch provider works standalone."""
        provider = FakeProvider()
        results = provider.embed_batch(["a", "b"])
        assert len(results) == 2

    def test_direct_provider_properties(self) -> None:
        """Verify provider properties return configured values."""
        provider = FakeProvider(model="m", dimension=256)
        assert provider.model_name == "m"
        assert provider.embedding_dimension == 256
