"""
Global exception handlers for the ResearchMind AI platform.

Maps domain exceptions to appropriate HTTP responses so that route
handlers never need to catch exceptions themselves.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
