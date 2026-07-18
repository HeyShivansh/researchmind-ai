"""Semantic retrieval service.

``RetrievalService`` orchestrates the end-to-end semantic retrieval
pipeline:

    Query → EmbeddingService → QdrantService → ChunkRepository → RetrievedChunk

No BM25, no reranking, no LLM — pure vector similarity retrieval.
Each step's exceptions are translated into domain exceptions from
``app.retrieval.exceptions``.
"""

from __future__ import annotations

from uuid import UUID

from app.embeddings import EmbeddingResult, EmbeddingService
from app.embeddings.exceptions import EmbeddingError, EmptyEmbeddingError
from app.repositories.chunk_repository import ChunkRepository
from app.retrieval.exceptions import (
    ChunkLookupError,
    QueryEmbeddingError,
    RetrievalError,
    SemanticSearchError,
)
from app.retrieval.models import RetrievedChunk
from app.vectorstore import QdrantService, SearchResult
from app.vectorstore.exceptions import SearchError


class RetrievalService:
    """Orchestrates the semantic retrieval pipeline.

    Accepts a user query, embeds it, searches Qdrant for similar
    vectors, looks up the corresponding chunks in PostgreSQL, and
    returns ordered results.

    Parameters
    ----------
    embedding_service : EmbeddingService
        Service for embedding the query text.
    qdrant_service : QdrantService
        Service for vector similarity search.
    chunk_repository : ChunkRepository
        Repository for looking up chunk text by ID.

    Examples
    --------
    >>> results = retrieval_service.semantic_search(
    ...     "What is attention?",
    ...     top_k=5,
    ... )
    >>> len(results)
    5
    >>> results[0].score
    0.95
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        chunk_repository: ChunkRepository,
    ) -> None:
        self._embedding_service = embedding_service
        self._qdrant_service = qdrant_service
        self._chunk_repository = chunk_repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_query(self, query: str) -> EmbeddingResult:
        """Embed a query string for retrieval.

        This is exposed separately so callers can cache the query
        vector if needed.

        Parameters
        ----------
        query : str
            The user's query text.  Must be non-empty.

        Returns
        -------
        EmbeddingResult
            The embedding vector with model metadata.

        Raises
        ------
        QueryEmbeddingError
            If the query is empty or the embedding provider fails.
        """
        try:
            return self._embedding_service.embed_text(query)
        except EmptyEmbeddingError as exc:
            raise QueryEmbeddingError(str(exc)) from exc
        except EmbeddingError as exc:
            raise QueryEmbeddingError(
                f"Failed to embed query: {exc}"
            ) from exc

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Run the full semantic retrieval pipeline.

        Parameters
        ----------
        query : str
            The user's query text.  Must be non-empty.
        top_k : int
            Number of results to return (must be > 0).

        Returns
        -------
        list[RetrievedChunk]
            Retrieved chunks ordered by similarity score (highest
            first).  Each result combines the Qdrant score with the
            full chunk text from PostgreSQL.

        Raises
        ------
        RetrievalError
            Base exception for all retrieval failures.  More specific
            subtypes (``QueryEmbeddingError``, ``SemanticSearchError``,
            ``ChunkLookupError``) are raised for step-specific
            failures.
        """
        self._validate_query(query)
        self._validate_top_k(top_k)

        # 1. Embed the query
        embedding = self._embed_query_internal(query)

        # 2. Search Qdrant
        search_results = self._search_qdrant(embedding.vector, top_k)

        if not search_results:
            return []

        # 3. Look up chunks from PostgreSQL
        chunk_ids = [r.chunk_id for r in search_results]
        chunks = self._lookup_chunks(chunk_ids)

        # 4. Reorder to match Qdrant ranking and assemble results
        return self._build_results(search_results, chunks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_query(query: str) -> None:
        """Reject empty or whitespace-only queries."""
        if not query or not query.strip():
            raise QueryEmbeddingError(
                "Query must not be empty or whitespace-only."
            )

    @staticmethod
    def _validate_top_k(top_k: int) -> None:
        """Reject non-positive ``top_k`` values."""
        if top_k <= 0:
            raise RetrievalError(
                f"top_k must be positive, got {top_k}."
            )

    def _embed_query_internal(self, query: str) -> EmbeddingResult:
        """Embed the query, translating embedding errors.

        Parameters
        ----------
        query : str
            The pre-validated query text.

        Returns
        -------
        EmbeddingResult
            The embedding vector.

        Raises
        ------
        QueryEmbeddingError
            If the embedding provider fails.
        """
        try:
            return self._embedding_service.embed_text(query)
        except EmbeddingError as exc:
            raise QueryEmbeddingError(
                f"Failed to embed query: {exc}"
            ) from exc

    def _search_qdrant(
        self,
        vector: list[float],
        top_k: int,
    ) -> list[SearchResult]:
        """Search Qdrant, translating vector-store errors.

        Parameters
        ----------
        vector : list[float]
            The query embedding vector.
        top_k : int
            Number of results to request.

        Returns
        -------
        list[SearchResult]
            Ordered search results from Qdrant.

        Raises
        ------
        SemanticSearchError
            If the vector search fails.
        """
        try:
            return self._qdrant_service.search(
                vector=vector,
                limit=top_k,
            )
        except SearchError as exc:
            raise SemanticSearchError(str(exc)) from exc

    def _lookup_chunks(
        self,
        chunk_ids: list[UUID],
    ) -> dict[UUID, RetrievedChunk]:
        """Look up chunks by ID in a single database query.

        Returns a dict keyed by chunk_id for fast reordering.
        Missing chunks are silently skipped.

        Parameters
        ----------
        chunk_ids : list[UUID]
            The chunk IDs to look up, in Qdrant rank order.

        Returns
        -------
        dict[UUID, RetrievedChunk]
            Retrieved chunks keyed by their ID.  Chunks that were not
            found in the database are omitted.

        Raises
        ------
        ChunkLookupError
            If the database query fails.
        """
        try:
            orm_chunks = self._chunk_repository.get_by_ids(chunk_ids)
        except Exception as exc:
            raise ChunkLookupError(
                f"Failed to look up chunks: {exc}"
            ) from exc

        result: dict[UUID, RetrievedChunk] = {}
        for c in orm_chunks:
            # Only build the result with what we have; score will
            # be filled in by the caller.
            result[c.id] = RetrievedChunk(
                chunk_id=c.id,
                paper_id=c.paper_id,
                text=c.text,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                score=0.0,  # placeholder, overwritten in _build_results
            )
        return result

    @staticmethod
    def _build_results(
        search_results: list[SearchResult],
        chunk_map: dict[UUID, RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Assemble final results in Qdrant rank order.

        Chunks that are present in the search results but missing
        from the database are silently skipped.

        Parameters
        ----------
        search_results : list[SearchResult]
            Ordered results from Qdrant.
        chunk_map : dict[UUID, RetrievedChunk]
            Chunks keyed by ID, as returned by ``_lookup_chunks``.

        Returns
        -------
        list[RetrievedChunk]
            Final results ordered by similarity score.
        """
        results: list[RetrievedChunk] = []
        for sr in search_results:
            chunk = chunk_map.get(sr.chunk_id)
            if chunk is None:
                continue
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    paper_id=chunk.paper_id,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    score=sr.score,
                )
            )
        return results
