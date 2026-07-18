"""
Paper service — business logic and transaction management for the
Paper domain aggregate.

The service layer is the sole owner of database transactions and
raises domain exceptions that are Framework-agnostic (no HTTP or
FastAPI dependency).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.chunking import BaseChunker, DocumentChunk
from app.core.config import settings
from app.exceptions.paper import DuplicatePaperError, PaperNotFoundError
from app.models.paper import Paper
from app.processing import DocumentProcessor, ProcessedDocument
from app.repositories.paper_repository import PaperRepository
from app.schemas.paper import PaperCreate
from app.services.chunk_persistence_service import ChunkPersistenceService
from app.storage.file_storage import FileStorage
from app.storage.validators import PDFValidator


class PaperService:
    """
    Service for Paper business operations.

    Owns all transaction management (commit, rollback, refresh) and
    coordinates with the repository layer.  The repository is an
    internal implementation detail and is instantiated by the service.

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use for all database operations.
    file_storage : FileStorage or None
        Storage layer for PDF files.  Required for upload operations.

    Examples
    --------
    >>> service = PaperService(db_session)
    >>> paper = service.create_paper(PaperCreate(title="...", pdf_path="..."))
    """

    def __init__(
        self,
        session: Session,
        file_storage: FileStorage | None = None,
        document_processor: DocumentProcessor | None = None,
        chunker: BaseChunker | None = None,
        chunk_persistence_service: ChunkPersistenceService | None = None,
    ) -> None:
        self._repository = PaperRepository(session)
        self._session = session
        self._file_storage = file_storage
        self._document_processor = document_processor
        self._chunker = chunker
        self._chunk_persistence_service = chunk_persistence_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_paper(self, paper: PaperCreate) -> Paper:
        """
        Create a new paper.

        If the paper has a DOI, ensures no other paper with that DOI
        already exists before creating it.

        Parameters
        ----------
        paper : PaperCreate
            The validated creation data for the new paper.

        Returns
        -------
        Paper
            The newly created ORM instance, committed and refreshed.

        Raises
        ------
        DuplicatePaperError
            If another paper with the same DOI already exists.
        """
        if paper.doi is not None:
            existing = self._repository.get_by_doi(paper.doi)
            if existing is not None:
                raise DuplicatePaperError(paper.doi)

        instance = self._repository.create(**paper.model_dump())

        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        self._session.refresh(instance)
        return instance

    def get_paper(self, paper_id: UUID) -> Paper:
        """
        Retrieve a paper by its unique identifier.

        Parameters
        ----------
        paper_id : UUID
            The identifier of the paper to retrieve.

        Returns
        -------
        Paper
            The matching ORM instance.

        Raises
        ------
        PaperNotFoundError
            If no paper with ``paper_id`` exists.
        """
        paper = self._repository.get_by_id(paper_id)
        if paper is None:
            raise PaperNotFoundError(paper_id)
        return paper

    def list_papers(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Retrieve a paginated list of all papers.

        Parameters
        ----------
        skip : int
            Number of records to skip (OFFSET). Defaults to 0.
        limit : int
            Maximum number of records to return. Defaults to 100.

        Returns
        -------
        list[Paper]
            A list of Paper ORM instances.
        """
        return self._repository.list(skip=skip, limit=limit)

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_paper(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        title: str | None = None,
        doi: str | None = None,
        publication_year: int | None = None,
        abstract: str | None = None,
    ) -> Paper:
        """
        Upload a PDF and create a Paper record atomically.

        Validates the file, saves it to disk, processes and chunks the
        PDF content, and persists both the Paper and its chunks in a
        single transaction.  If any step fails, the database is rolled
        back and the uploaded PDF is deleted, leaving no orphan records.

        Parameters
        ----------
        file_bytes : bytes
            Raw bytes of the uploaded PDF.
        filename : str
            Original filename from the upload (used for extension
            validation only).
        title : str or None
            Paper title.  Defaults to the UUID-based filename if
            not provided.
        doi : str or None
            Digital Object Identifier.
        publication_year : int or None
            Year of publication.
        abstract : str or None
            Paper abstract.

        Returns
        -------
        Paper
            The newly created ORM instance, committed and refreshed.

        Raises
        ------
        DuplicatePaperError
            If another paper with the same DOI already exists.
        FileValidationError
            If the file fails extension, magic-bytes, or size checks.
        FileSaveError
            If the file could not be written to disk.
        RuntimeError
            If the service was not configured with the required
            dependencies for upload (file_storage, document_processor,
            chunker, chunk_persistence_service).
        """
        self._assert_upload_dependencies()

        # -- Validate -------------------------------------------------------
        PDFValidator.validate_extension(filename)
        PDFValidator.validate_magic_bytes(file_bytes)
        PDFValidator.validate_size(file_bytes, settings.MAX_UPLOAD_SIZE_MB)

        # -- DOI uniqueness -------------------------------------------------
        if doi is not None:
            existing = self._repository.get_by_doi(doi)
            if existing is not None:
                raise DuplicatePaperError(doi)

        # -- Persist file ---------------------------------------------------
        file_uuid = uuid4()
        storage_filename = f"{file_uuid}.pdf"
        storage_path = self._file_storage.save_pdf(file_bytes, storage_filename)

        # -- Persist record (pre-emptively, to own the paper_id) ------------
        paper_title = title or f"Paper {file_uuid}"
        instance = self._repository.create(
            title=paper_title,
            abstract=abstract,
            doi=doi,
            publication_year=publication_year,
            pdf_path=storage_path,
        )
        # Flush so the paper gets an id, but don't commit yet.
        self._session.flush()

        try:
            # -- Process PDF ------------------------------------------------
            pdf_on_disk = Path(storage_path)
            if not pdf_on_disk.is_absolute():
                pdf_on_disk = Path(self._file_storage.root) / storage_path
            processed: ProcessedDocument = self._document_processor.process(
                pdf_on_disk
            )

            # -- Generate chunks --------------------------------------------
            chunks: list[DocumentChunk] = self._chunker.chunk(processed)

            # -- Persist chunks ---------------------------------------------
            self._chunk_persistence_service.persist_chunks(
                paper_id=instance.id,
                chunks=chunks,
            )

            # -- Commit atomically ------------------------------------------
            self._session.commit()
        except Exception:
            self._session.rollback()
            self._file_storage.delete_pdf(storage_path)
            raise

        self._session.refresh(instance)
        return instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assert_upload_dependencies(self) -> None:
        """
        Verify that all dependencies required for upload are available.

        Raises
        ------
        RuntimeError
            If any required dependency is ``None``.
        """
        missing: list[str] = []
        if self._file_storage is None:
            missing.append("file_storage")
        if self._document_processor is None:
            missing.append("document_processor")
        if self._chunker is None:
            missing.append("chunker")
        if self._chunk_persistence_service is None:
            missing.append("chunk_persistence_service")
        if missing:
            raise RuntimeError(
                "PaperService requires the following dependencies for "
                f"upload operations: {', '.join(missing)}"
            )
