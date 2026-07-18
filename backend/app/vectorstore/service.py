"""Qdrant vector store service.

``QdrantService`` is the sole component responsible for interacting
with Qdrant.  It wraps the ``qdrant-client`` API and translates
library-specific exceptions into domain exceptions from
``app.vectorstore.exceptions``.

PostgreSQL remains the source of truth for chunk text.  Qdrant stores
only vectors and a lightweight payload (``chunk_id``, ``paper_id``,
``page_number``, ``chunk_index``).
"""

from __future__ import annotations

from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.vectorstore.exceptions import (
    CollectionError,
    DeleteError,
    SearchError,
    UpsertError,
)
from app.vectorstore.models import SearchResult

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_COLLECTION_NAME: str = "researchmind"


class QdrantService:
    """Vector store service backed by Qdrant.

    The collection is created automatically on first use if it does
    not exist.  All collection, upsert, search, and delete operations
    go through this single class.

    Parameters
    ----------
    client : QdrantClient
        An initialised ``QdrantClient`` instance (sync).  The caller
        is responsible for providing the connection configuration.
    collection_name : str
        Name of the Qdrant collection to use.
        Defaults to ``researchmind``.
    vector_dimension : int
        Dimensionality of the embedding vectors.  Must match the
        configured embedding provider.

    Examples
    --------
    >>> from qdrant_client import QdrantClient
    >>> client = QdrantClient(url="http://localhost:6333")
    >>> service = QdrantService(client, vector_dimension=768)
    >>> results = service.search([0.1] * 768, limit=5)
    """

    def __init__(
        self,
        client: QdrantClient,
        vector_dimension: int,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._vector_dimension = vector_dimension

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def collection_name(self) -> str:
        """Return the configured Qdrant collection name."""
        return self._collection_name

    @property
    def vector_dimension(self) -> int:
        """Return the configured vector dimension."""
        return self._vector_dimension

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def collection_exists(self) -> bool:
        """Check whether the configured collection exists in Qdrant.

        Returns
        -------
        bool
            ``True`` if the collection exists, ``False`` otherwise.

        Raises
        ------
        CollectionError
            If the existence check fails.
        """
        try:
            return self._client.collection_exists(
                collection_name=self._collection_name
            )
        except Exception as exc:
            raise CollectionError(
                f"Failed to check if collection "
                f"'{self._collection_name}' exists: {exc}",
                collection_name=self._collection_name,
            ) from exc

    def create_collection(self) -> None:
        """Create the configured collection if it does not exist.

        Uses cosine similarity and the configured vector dimension.
        If the collection already exists, this is a no-op.

        Raises
        ------
        CollectionError
            If collection creation fails (excluding the case where
            the collection already exists).
        """
        if self.collection_exists():
            return

        try:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=self._vector_dimension,
                    distance=models.Distance.COSINE,
                ),
            )
        except Exception as exc:
            raise CollectionError(
                f"Failed to create collection "
                f"'{self._collection_name}': {exc}",
                collection_name=self._collection_name,
            ) from exc

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    def upsert_chunk(
        self,
        chunk_id: UUID,
        vector: list[float],
        paper_id: UUID,
        page_number: int,
        chunk_index: int,
    ) -> None:
        """Upsert a single chunk's vector and payload into Qdrant.

        Parameters
        ----------
        chunk_id : UUID
            Unique identifier for this chunk (used as the Qdrant
            point ID).
        vector : list[float]
            The embedding vector.
        paper_id : UUID
            The paper this chunk belongs to.
        page_number : int
            1-based page number from the source document.
        chunk_index : int
            Global index of this chunk across the entire document.

        Raises
        ------
        UpsertError
            If the upsert operation fails.
        """
        self.upsert_chunks([(chunk_id, vector, paper_id, page_number, chunk_index)])

    def upsert_chunks(
        self,
        chunks: list[tuple[UUID, list[float], UUID, int, int]],
    ) -> None:
        """Upsert multiple chunks in a single batch operation.

        Each tuple is ``(chunk_id, vector, paper_id, page_number,
        chunk_index)``.

        Parameters
        ----------
        chunks : list[tuple[UUID, list[float], UUID, int, int]]
            One tuple per chunk to upsert.

        Raises
        ------
        UpsertError
            If the batch upsert operation fails.
        """
        if not chunks:
            return

        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=[
                    models.PointStruct(
                        id=str(chunk_id),
                        vector=vector,
                        payload={
                            "chunk_id": str(chunk_id),
                            "paper_id": str(paper_id),
                            "page_number": page_number,
                            "chunk_index": chunk_index,
                        },
                    )
                    for chunk_id, vector, paper_id, page_number, chunk_index in chunks
                ],
            )
        except Exception as exc:
            raise UpsertError(
                f"Failed to upsert {len(chunks)} point(s) into "
                f"collection '{self._collection_name}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        vector: list[float],
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search for the most similar vectors in the collection.

        Parameters
        ----------
        vector : list[float]
            The query embedding vector.
        limit : int
            Maximum number of results to return (default 10).

        Returns
        -------
        list[SearchResult]
            Ordered list of ``SearchResult`` objects, from most to
            least similar.

        Raises
        ------
        SearchError
            If the search operation fails.
        """
        try:
            response = self._client.query_points(
                collection_name=self._collection_name,
                query=vector,
                limit=limit,
            )
            results = response.points
        except Exception as exc:
            raise SearchError(
                f"Failed to search collection "
                f"'{self._collection_name}': {exc}"
            ) from exc

        return [
            SearchResult(
                chunk_id=UUID(payload["chunk_id"]),
                score=point.score,
            )
            for point in results
            if (payload := point.payload)
        ]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_paper(self, paper_id: UUID) -> None:
        """Delete all vectors belonging to a paper.

        Parameters
        ----------
        paper_id : UUID
            The paper whose vectors should be removed.

        Raises
        ------
        DeleteError
            If the delete operation fails.
        """
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="paper_id",
                            match=models.MatchValue(
                                value=str(paper_id)
                            ),
                        )
                    ],
                ),
            )
        except Exception as exc:
            raise DeleteError(
                f"Failed to delete points for paper "
                f"'{paper_id}' from collection "
                f"'{self._collection_name}': {exc}"
            ) from exc
