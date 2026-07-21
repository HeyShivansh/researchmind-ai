"""
Service dependencies for the ResearchMind AI platform.

Provides FastAPI-compatible dependencies that wire up service layer
and infrastructure instances for injection into route handlers.
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from qdrant_client import QdrantClient

from app.chunking import RecursiveCharacterChunker
from app.core.config import settings
from app.embeddings import BaseEmbeddingProvider, EmbeddingService
from app.embeddings.providers import GeminiEmbeddingProvider
from app.hybrid import HybridRetrievalService
from app.processing import DocumentProcessor
from app.repositories.chunk_repository import ChunkRepository
from app.retrieval import RetrievalService
from app.services.chunk_persistence_service import ChunkPersistenceService
from app.services.indexing_service import DocumentIndexingService
from app.services.paper_service import PaperService
from app.storage.file_storage import FileStorage
from app.vectorstore import QdrantService

from .database import get_db


@lru_cache(maxsize=1)
def get_file_storage() -> FileStorage:
    """
    FastAPI dependency that provides a singleton ``FileStorage`` instance.

    Returns
    -------
    FileStorage
        A shared storage instance wired to the application settings.
    """
    return FileStorage(settings)


@lru_cache(maxsize=1)
def get_document_processor() -> DocumentProcessor:
    """
    FastAPI dependency that provides a singleton ``DocumentProcessor`` instance.

    Returns
    -------
    DocumentProcessor
        A shared processor instance.
    """
    return DocumentProcessor()


@lru_cache(maxsize=1)
def get_chunker() -> RecursiveCharacterChunker:
    """
    FastAPI dependency that provides a singleton ``RecursiveCharacterChunker``
    instance.

    The chunk size and overlap are pulled from application settings.
    Current defaults (500 / 50) are suitable for scientific papers and
    are configurable via environment variables.

    Returns
    -------
    RecursiveCharacterChunker
        A shared chunker instance.
    """
    return RecursiveCharacterChunker(
        chunk_size=settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
    )


def get_chunk_persistence_service(
    db: Session = Depends(get_db),
) -> ChunkPersistenceService:
    """
    FastAPI dependency that provides a ``ChunkPersistenceService`` instance.

    Parameters
    ----------
    db : Session
        Database session obtained from ``get_db``.

    Returns
    -------
    ChunkPersistenceService
        A service instance wired to the provided database session.
    """
    return ChunkPersistenceService(db)


# ---------------------------------------------------------------------------
# Embedding dependencies
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    FastAPI dependency that provides a singleton embedding provider.

    The provider type is selected by ``settings.EMBEDDING_PROVIDER``.
    Currently only ``"gemini"`` is implemented; others will raise a
    ``RuntimeError``.

    Returns
    -------
    BaseEmbeddingProvider
        A shared embedding provider instance.

    Raises
    ------
    RuntimeError
        If the configured provider is not implemented.
    """
    if settings.EMBEDDING_PROVIDER == "gemini":
        return GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )

    msg = (
        f"Unknown or unimplemented embedding provider: "
        f"'{settings.EMBEDDING_PROVIDER}'.  Available: gemini."
    )
    raise RuntimeError(msg)


@lru_cache(maxsize=1)
def get_embedding_service(
    provider: BaseEmbeddingProvider = Depends(get_embedding_provider),
) -> EmbeddingService:
    """
    FastAPI dependency that provides a singleton ``EmbeddingService``.

    The service is wired to the embedding provider obtained from
    ``get_embedding_provider``.

    Returns
    -------
    EmbeddingService
        A shared embedding service instance.
    """
    return EmbeddingService(provider=provider)


# ---------------------------------------------------------------------------
# Vector store dependencies
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """
    FastAPI dependency that provides a singleton ``QdrantClient``.

    The client is configured from application settings (URL and API
    key).  No collection is created at this point — that happens
    lazily when ``QdrantService.create_collection()`` is called.

    Returns
    -------
    QdrantClient
        A shared Qdrant client instance.
    """
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
    )


@lru_cache(maxsize=1)
def get_qdrant_service(
    client: QdrantClient = Depends(get_qdrant_client),
) -> QdrantService:
    """
    FastAPI dependency that provides a singleton ``QdrantService``.

    The vector dimension is pulled from the embedding configuration
    so that vectors produced by the embedding service and stored in
    Qdrant always have compatible dimensions.

    Returns
    -------
    QdrantService
        A shared Qdrant service instance.
    """
    return QdrantService(
        client=client,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        vector_dimension=settings.QDRANT_VECTOR_DIMENSION,
    )


# ---------------------------------------------------------------------------
# Retrieval dependencies
# ---------------------------------------------------------------------------


def get_retrieval_service(
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> RetrievalService:
    """
    FastAPI dependency that provides a ``RetrievalService`` instance.

    Wires together the embedding service, Qdrant service, and chunk
    repository into a single retrieval pipeline.

    Parameters
    ----------
    db : Session
        Database session obtained from ``get_db``.
    embedding_service : EmbeddingService
        Service obtained from ``get_embedding_service``.
    qdrant_service : QdrantService
        Service obtained from ``get_qdrant_service``.

    Returns
    -------
    RetrievalService
        A retrieval service instance wired to the provided dependencies.
    """
    return RetrievalService(
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
        chunk_repository=ChunkRepository(db),
    )


# ---------------------------------------------------------------------------
# Hybrid retrieval dependencies
# ---------------------------------------------------------------------------


def get_hybrid_retrieval_service(
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> HybridRetrievalService:
    """
    FastAPI dependency that provides a ``HybridRetrievalService`` instance.

    Wires together the retrieval service and chunk repository with
    configurable top-k and fusion parameters.

    Parameters
    ----------
    db : Session
        Database session obtained from ``get_db``.
    retrieval_service : RetrievalService
        Service obtained from ``get_retrieval_service``.

    Returns
    -------
    HybridRetrievalService
        A hybrid retrieval service instance.
    """
    return HybridRetrievalService(
        retrieval_service=retrieval_service,
        chunk_repository=ChunkRepository(db),
        semantic_top_k=settings.HYBRID_SEMANTIC_TOP_K,
        keyword_top_k=settings.HYBRID_KEYWORD_TOP_K,
        fusion_k=settings.HYBRID_FUSION_K,
    )


def get_indexing_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> DocumentIndexingService:
    """
    FastAPI dependency that provides a ``DocumentIndexingService`` instance.

    Wires together the embedding service and Qdrant service for indexing
    document chunks into the vector store.

    Parameters
    ----------
    embedding_service : EmbeddingService
        Service obtained from ``get_embedding_service``.
    qdrant_service : QdrantService
        Service obtained from ``get_qdrant_service``.

    Returns
    -------
    DocumentIndexingService
        An indexing service instance wired to the provided dependencies.
    """
    return DocumentIndexingService(
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
    )


def get_paper_service(
    db: Session = Depends(get_db),
    file_storage: FileStorage = Depends(get_file_storage),
    document_processor: DocumentProcessor = Depends(get_document_processor),
    chunker: RecursiveCharacterChunker = Depends(get_chunker),
    chunk_persistence_service: ChunkPersistenceService = Depends(
        get_chunk_persistence_service
    ),
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> PaperService:
    """
    FastAPI dependency that provides a ``PaperService`` instance.

    Parameters
    ----------
    db : Session
        Database session obtained from ``get_db``.
    file_storage : FileStorage
        Storage layer obtained from ``get_file_storage``.
    document_processor : DocumentProcessor
        Processor obtained from ``get_document_processor``.
    chunker : RecursiveCharacterChunker
        Chunker obtained from ``get_chunker``.
    chunk_persistence_service : ChunkPersistenceService
        Chunk persistence service obtained from ``get_chunk_persistence_service``.
    indexing_service : DocumentIndexingService
        Indexing service obtained from ``get_indexing_service``.

    Returns
    -------
    PaperService
        A service instance wired to the provided dependencies.
    """
    return PaperService(
        db,
        file_storage=file_storage,
        document_processor=document_processor,
        chunker=chunker,
        chunk_persistence_service=chunk_persistence_service,
        indexing_service=indexing_service,
    )
