"""
Global exception handlers for the ResearchMind AI platform.

Maps domain exceptions to appropriate HTTP responses so that route
handlers never need to catch exceptions themselves.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import FileSaveError, FileValidationError
from app.exceptions.paper import DuplicatePaperError, PaperNotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all domain exception handlers on the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        The application instance to attach handlers to.
    """

    @app.exception_handler(DuplicatePaperError)
    async def duplicate_paper_handler(
        request: Request,
        exc: DuplicatePaperError,
    ) -> JSONResponse:
        """Return 409 Conflict when a duplicate DOI is detected."""
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )

    @app.exception_handler(PaperNotFoundError)
    async def paper_not_found_handler(
        request: Request,
        exc: PaperNotFoundError,
    ) -> JSONResponse:
        """Return 404 Not Found when a paper does not exist."""
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileValidationError)
    async def file_validation_error_handler(
        request: Request,
        exc: FileValidationError,
    ) -> JSONResponse:
        """Return 422 Unprocessable Entity when file validation fails."""
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileSaveError)
    async def file_save_error_handler(
        request: Request,
        exc: FileSaveError,
    ) -> JSONResponse:
        """Return 500 Internal Server Error when file persistence fails."""
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )
