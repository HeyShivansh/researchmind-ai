"""Hybrid retrieval service combining semantic and BM25 keyword search.

``HybridRetrievalService`` merges two retrieval strategies:

1. **Semantic search** via ``RetrievalService`` (embeddings → Qdrant)
2. **Keyword search** via BM25 (``rank-bm25`` over PostgreSQL chunk text)

Both result sets are combined using **Reciprocal Rank Fusion (RRF)**
with a configurable ``k`` parameter (default 60).
"""

from __future__ import annotations

from uuid import UUID

from rank_bm25 import BM25Okapi

from app.hybrid.exceptions import BM25IndexError, HybridRetrievalError
from app.repositories.chunk_repository import ChunkRepository
from app.retrieval.models import RetrievedChunk
from app.retrieval.service import RetrievalService

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_SEMANTIC_TOP_K: int = 10
DEFAULT_KEYWORD_TOP_K: int = 10
DEFAULT_FUSION_K: int = 60


class HybridRetrievalService:
    """Combines semantic and BM25 retrieval with RRF fusion.

    Parameters
    ----------
    retrieval_service : RetrievalService
        Service for semantic (vector) retrieval.
    chunk_repository : ChunkRepository
        Repository for fetching chunk texts for BM25 indexing.
    semantic_top_k : int
        Number of results to fetch from semantic search (default 10).
    keyword_top_k : int
        Number of results to fetch from BM25 keyword search (default 10).
    fusion_k : int
        RRF constant for score calculation (default 60).

    Examples
    --------
    >>> service = HybridRetrievalService(retrieval_service, chunk_repo)
    >>> results = service.hybrid_search("What is attention?")
    >>> len(results)
    10
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        chunk_repository: ChunkRepository,
        semantic_top_k: int = DEFAULT_SEMANTIC_TOP_K,
        keyword_top_k: int = DEFAULT_KEYWORD_TOP_K,
        fusion_k: int = DEFAULT_FUSION_K,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._chunk_repository = chunk_repository
        self._semantic_top_k = semantic_top_k
        self._keyword_top_k = keyword_top_k
        self._fusion_k = fusion_k

        # BM25 index — built lazily on first keyword/hybrid search.
        self._bm25: BM25Okapi | None = None
        self._bm25_ids: list[UUID] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rebuild_index(self) -> None:
        """Rebuild the BM25 index from all chunk texts.

        Call this after uploading new papers to keep the index in
        sync with the database.

        Raises
        ------
        BM25IndexError
            If fetching chunk texts or building the index fails.
        """
        try:
            texts = self._chunk_repository.get_all_texts()
        except Exception as exc:
            raise BM25IndexError(
                f"Failed to fetch chunk texts for BM25 index: {exc}"
            ) from exc

        if not texts:
            self._bm25 = None
            self._bm25_ids = []
            return

        try:
            self._bm25_ids = [chunk_id for chunk_id, _ in texts]
            tokenized_corpus = [text.lower().split() for _, text in texts]
            self._bm25 = BM25Okapi(tokenized_corpus)
        except Exception as exc:
            raise BM25IndexError(
                f"Failed to build BM25 index: {exc}"
            ) from exc

    def semantic_search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Run semantic search via ``RetrievalService.semantic_search``.

        Parameters
        ----------
        query : str
            The user's query text.
        top_k : int or None
            Override for the configured ``semantic_top_k``.
            Defaults to the instance's configured value.

        Returns
        -------
        list[RetrievedChunk]
            Results ordered by semantic similarity.
        """
        return self._retrieval_service.semantic_search(
            query,
            top_k=top_k or self._semantic_top_k,
        )

    def keyword_search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Run BM25 keyword search over all chunk texts.

        The BM25 index is built lazily on the first call.

        Parameters
        ----------
        query : str
            The user's query text.  Must be non-empty.
        top_k : int or None
            Override for the configured ``keyword_top_k``.
            Defaults to the instance's configured value.

        Returns
        -------
        list[RetrievedChunk]
            Results ordered by BM25 relevance score.
        """
        limit = top_k or self._keyword_top_k
        self._ensure_index()

        if self._bm25 is None or not self._bm25_ids:
            return []

        tokenized_query = query.lower().split()
        try:
            scores = self._bm25.get_scores(tokenized_query)
        except Exception as exc:
            raise BM25IndexError(
                f"Failed to score query with BM25: {exc}"
            ) from exc

        # Pair scores with IDs and sort by score descending
        scored: list[tuple[float, UUID]] = [
            (score, chunk_id)
            for score, chunk_id in zip(scores, self._bm25_ids, strict=True)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Filter out zero-score results (no actual matches) and take top-k
        top_ids = [
            chunk_id
            for score, chunk_id in scored
            if score > 0
        ][:limit]

        if not top_ids:
            return []

        # Look up full chunk details from the database
        return self._build_keyword_results(top_ids, scored)

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Run hybrid semantic + keyword search with RRF fusion.

        Parameters
        ----------
        query : str
            The user's query text.  Must be non-empty.
        top_k : int
            Number of results to return (must be > 0).

        Returns
        -------
        list[RetrievedChunk]
            Results ordered by fused RRF score (highest first).
            Chunks appearing in both result sets receive higher
            scores due to the RRF formula.

        Raises
        ------
        HybridRetrievalError
            If any step of the retrieval pipeline fails.
        """
        self._validate_query(query)
        self._validate_top_k(top_k)

        semantic_results = self.semantic_search(query)
        keyword_results = self.keyword_search(query)

        return self._rrf_fuse(
            semantic_results,
            keyword_results,
            k=self._fusion_k,
            top_k=top_k,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_index(self) -> None:
        """Build the BM25 index if it hasn't been built yet."""
        if self._bm25 is None:
            self.rebuild_index()

    @staticmethod
    def _validate_query(query: str) -> None:
        """Reject empty or whitespace-only queries."""
        if not query or not query.strip():
            raise HybridRetrievalError(
                "Query must not be empty or whitespace-only."
            )

    @staticmethod
    def _validate_top_k(top_k: int) -> None:
        """Reject non-positive ``top_k`` values."""
        if top_k <= 0:
            raise HybridRetrievalError(
                f"top_k must be positive, got {top_k}."
            )

    def _build_keyword_results(
        self,
        top_ids: list[UUID],
        scored: list[tuple[float, UUID]],
    ) -> list[RetrievedChunk]:
        """Look up chunk details and build results preserving BM25 rank."""
        try:
            orm_chunks = self._chunk_repository.get_by_ids(top_ids)
        except Exception as exc:
            raise BM25IndexError(
                f"Failed to look up BM25 result chunks: {exc}"
            ) from exc

        # Build a score map from the scored list
        score_map: dict[UUID, float] = {chunk_id: score for score, chunk_id in scored}

        chunk_map: dict[UUID, RetrievedChunk] = {}
        for c in orm_chunks:
            chunk_map[c.id] = RetrievedChunk(
                chunk_id=c.id,
                paper_id=c.paper_id,
                text=c.text,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                score=score_map.get(c.id, 0.0),
            )

        # Reorder to match BM25 ranking
        results: list[RetrievedChunk] = []
        for chunk_id in top_ids:
            chunk = chunk_map.get(chunk_id)
            if chunk is not None:
                results.append(chunk)
        return results

    @staticmethod
    def _rrf_fuse(
        semantic_results: list[RetrievedChunk],
        keyword_results: list[RetrievedChunk],
        k: int = 60,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Merge two ranked result lists using Reciprocal Rank Fusion.

        Parameters
        ----------
        semantic_results : list[RetrievedChunk]
            Results from semantic search, ordered by score descending.
        keyword_results : list[RetrievedChunk]
            Results from keyword search, ordered by score descending.
        k : int
            RRF constant (default 60).
        top_k : int
            Number of results to return.

        Returns
        -------
        list[RetrievedChunk]
            Fused results ordered by RRF score descending.  Chunks
            present in both lists receive a higher fused score.
        """
        fused: dict[UUID, float] = {}
        chunk_map: dict[UUID, RetrievedChunk] = {}

        # Semantic contributions (1-based rank)
        for rank, result in enumerate(semantic_results, start=1):
            fused[result.chunk_id] = 1.0 / (k + rank)
            chunk_map[result.chunk_id] = result

        # Keyword contributions — additive for duplicates
        for rank, result in enumerate(keyword_results, start=1):
            contribution = 1.0 / (k + rank)
            if result.chunk_id in fused:
                fused[result.chunk_id] += contribution
            else:
                fused[result.chunk_id] = contribution
            chunk_map[result.chunk_id] = result

        # Sort by fused score descending
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)

        # Build final result list
        results: list[RetrievedChunk] = []
        for chunk_id, score in ranked[:top_k]:
            chunk = chunk_map[chunk_id]
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    paper_id=chunk.paper_id,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    score=score,
                )
            )
        return results
