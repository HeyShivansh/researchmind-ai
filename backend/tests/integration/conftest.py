"""Pytest fixtures for the end-to-end integration test suite.

Wires together real application components (DocumentProcessor, chunker,
QdrantService, HybridRetrievalService) with a fake embedding provider
that avoids external API calls.  PostgreSQL and Qdrant must be running
(see ``docker-compose.yml``).

Only the external embedding provider is mocked — everything else
executes exactly as in production.
"""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from app.chunking import RecursiveCharacterChunker
from app.core.config import Settings
from app.embeddings import BaseEmbeddingProvider, EmbeddingResult, EmbeddingService
from app.hybrid import HybridRetrievalService
from app.processing import DocumentProcessor
from app.repositories.chunk_repository import ChunkRepository
from app.retrieval import RetrievalService
from app.services.chunk_persistence_service import ChunkPersistenceService
from app.services.indexing_service import DocumentIndexingService
from app.services.paper_service import PaperService
from app.storage.file_storage import FileStorage
from app.vectorstore import QdrantService

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMBEDDING_DIMENSION: int = 8
TEST_QDRANT_URL: str = "http://localhost:6333"
CHUNK_SIZE: int = 200
CHUNK_OVERLAP: int = 20

# ---------------------------------------------------------------------------
# Fake embedding provider (deterministic, no external API)
# ---------------------------------------------------------------------------


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Produces deterministic embeddings using MD5-based hashing.

    The same input text always produces the same vector.  Different
    texts produce different vectors, enabling meaningful similarity
    comparisons within the test suite.
    """

    def __init__(self, dimension: int = EMBEDDING_DIMENSION) -> None:
        self._dimension = dimension
        self._model = "deterministic-test"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def embedding_dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> EmbeddingResult:
        vector = self._hash_to_vector(text)
        return EmbeddingResult(
            vector=vector,
            model_name=self._model,
            dimension=self._dimension,
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [self.embed_text(t) for t in texts]

    def _hash_to_vector(self, text: str) -> list[float]:
        """Convert text to a deterministic float vector via word-level MD5.

        Each word contributes its hash to the vector, so texts sharing
        words (e.g. query and document) produce more similar vectors.
        """
        words = text.lower().split()
        if not words:
            return [0.0] * self._dimension

        # Sum word-level vectors, then normalize
        vec_sum = [0.0] * self._dimension
        for word in words:
            digest = hashlib.md5(word.encode()).digest()
            for i in range(self._dimension):
                vec_sum[i] += digest[i % len(digest)] / 255.0

        avg = sum(vec_sum) / (self._dimension * len(words))
        vector = [(v / len(words)) - avg for v in vec_sum]

        # Deterministic normalization to unit length for cosine sim
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


# ---------------------------------------------------------------------------
# Session-scoped: Qdrant
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qdrant_client() -> Generator[QdrantClient, None, None]:
    """Provide a ``QdrantClient`` connected to the local Docker instance."""
    client = QdrantClient(url=TEST_QDRANT_URL)
    yield client


@pytest.fixture(scope="session")
def test_collection_name() -> Generator[str, None, None]:
    """Generate and clean up a unique test collection name."""
    name = f"int_test_{uuid4().hex[:12]}"
    yield name
    # Session-level cleanup: drop the collection
    client = QdrantClient(url=TEST_QDRANT_URL)
    try:
        client.delete_collection(name)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Per-test: services (session-scoped dependencies)
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_storage(tmp_path: Path) -> FileStorage:
    """Provide a ``FileStorage`` rooted at a temporary directory."""
    test_settings = Settings(STORAGE_ROOT=str(tmp_path))
    return FileStorage(test_settings)


@pytest.fixture()
def processor() -> DocumentProcessor:
    """Provide a real ``DocumentProcessor``."""
    return DocumentProcessor()


@pytest.fixture()
def chunker() -> RecursiveCharacterChunker:
    """Provide a real chunker with small size for deterministic results."""
    return RecursiveCharacterChunker(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )


@pytest.fixture()
def embedding_provider() -> DeterministicEmbeddingProvider:
    """Provide the deterministic fake embedding provider."""
    return DeterministicEmbeddingProvider(dimension=EMBEDDING_DIMENSION)


@pytest.fixture()
def embedding_service(
    embedding_provider: DeterministicEmbeddingProvider,
) -> EmbeddingService:
    """Provide a real ``EmbeddingService`` with the fake provider."""
    return EmbeddingService(provider=embedding_provider)


@pytest.fixture()
def qdrant_service(
    qdrant_client: QdrantClient,
    test_collection_name: str,
) -> Generator[QdrantService, None, None]:
    """Provide a ``QdrantService`` with a dedicated test collection.

    The collection is created before each test and all points are
    cleared afterward for per-test isolation.
    """
    from qdrant_client.http import models

    # Ensure a clean slate: drop and recreate the collection
    try:
        qdrant_client.delete_collection(collection_name=test_collection_name)
    except Exception:
        pass

    svc = QdrantService(
        client=qdrant_client,
        collection_name=test_collection_name,
        vector_dimension=EMBEDDING_DIMENSION,
    )
    svc.create_collection()
    yield svc

    # Per-test cleanup: delete all points via Filter
    try:
        qdrant_client.delete(
            collection_name=test_collection_name,
            points_selector=models.Filter(must=[]),
        )
    except Exception:
        pass


@pytest.fixture()
def chunk_persistence_service(
    db_session: Session,
) -> ChunkPersistenceService:
    """Provide a real ``ChunkPersistenceService``."""
    return ChunkPersistenceService(db_session)


@pytest.fixture()
def chunk_repository(db_session: Session) -> ChunkRepository:
    """Provide a real ``ChunkRepository``."""
    return ChunkRepository(db_session)


@pytest.fixture()
def indexing_service(
    embedding_service: EmbeddingService,
    qdrant_service: QdrantService,
) -> DocumentIndexingService:
    """Provide a ``DocumentIndexingService`` wired for test uploads."""
    return DocumentIndexingService(
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
    )


@pytest.fixture()
def paper_service(
    db_session: Session,
    tmp_storage: FileStorage,
    processor: DocumentProcessor,
    chunker: RecursiveCharacterChunker,
    chunk_persistence_service: ChunkPersistenceService,
    indexing_service: DocumentIndexingService,
) -> PaperService:
    """Provide a ``PaperService`` wired for upload operations with indexing."""
    return PaperService(
        session=db_session,
        file_storage=tmp_storage,
        document_processor=processor,
        chunker=chunker,
        chunk_persistence_service=chunk_persistence_service,
        indexing_service=indexing_service,
    )


@pytest.fixture()
def retrieval_service(
    embedding_service: EmbeddingService,
    qdrant_service: QdrantService,
    chunk_repository: ChunkRepository,
) -> RetrievalService:
    """Provide a real ``RetrievalService``."""
    return RetrievalService(
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
        chunk_repository=chunk_repository,
    )


@pytest.fixture()
def hybrid_service(
    retrieval_service: RetrievalService,
    chunk_repository: ChunkRepository,
) -> HybridRetrievalService:
    """Provide a real ``HybridRetrievalService``.

    Uses small top_k values and the configured fusion_k for
    deterministic, fast tests.
    """
    return HybridRetrievalService(
        retrieval_service=retrieval_service,
        chunk_repository=chunk_repository,
        semantic_top_k=10,
        keyword_top_k=10,
        fusion_k=60,
    )
