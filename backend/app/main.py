"""
Application entrypoint for the ResearchMind AI platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger

from app.api import auth_router, health_router, paper_router, search_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.database.session import engine

logger = get_logger("researchmind")


def _validate_production_settings() -> None:
    """
    Fail-fast validation of required production environment variables.

    Raises RuntimeError on startup if critical settings are missing or
    use default/insecure values.  This prevents the application from
    running with a misconfigured environment.
    """
    if settings.APP_ENV != "production":
        return  # dev/staging: allow defaults for convenience

    errors: list[str] = []

    if not settings.GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    if not settings.SECRET_KEY or "change-me" in settings.SECRET_KEY.lower():
        errors.append("SECRET_KEY must be set to a secure random value")
    if not settings.POSTGRES_PASSWORD or settings.POSTGRES_PASSWORD == "researchmind":
        errors.append("POSTGRES_PASSWORD must be changed from the default")

    if errors:
        raise RuntimeError(
            "Production environment validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def _ensure_qdrant_collection() -> None:
    """
    Ensure the Qdrant collection exists, creating it if necessary.

    This runs once at application startup so that search endpoints
    do not fail with "Collection doesn't exist" on the first request.
    Failures are logged but do **not** prevent the app from starting,
    since Qdrant may not be fully initialized yet.
    """
    try:
        from qdrant_client import QdrantClient

        from app.vectorstore import QdrantService

        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
        qdrant_service = QdrantService(
            client=client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vector_dimension=settings.QDRANT_VECTOR_DIMENSION,
        )
        qdrant_service.create_collection()
        logger.info(
            "Qdrant collection ensured",
            collection=settings.QDRANT_COLLECTION_NAME,
        )
        client.close()
    except Exception as exc:
        logger.warning(
            "Could not verify Qdrant collection at startup — "
            "it will be created on first upload if needed",
            error=str(exc),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    - Startup: validate production settings, ensure Qdrant collection exists.
    - Shutdown: cleanly close database connections.
    """
    # Startup
    _validate_production_settings()
    _ensure_qdrant_collection()
    logger.info("Application started", env=settings.APP_ENV)
    yield
    # Shutdown — clean up connections
    logger.info("Application shutting down, disposing database connections...")
    engine.dispose()
    logger.info("Database connections disposed.")


# Configure structured logging before the app is created
setup_logging(env=settings.APP_ENV)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js frontend to access the API
# ---------------------------------------------------------------------------
_cors_origins = getattr(settings, "CORS_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in _cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(paper_router)
app.include_router(search_router)

register_exception_handlers(app)


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple health-check payload for the API root."""
    return {
        "message": "ResearchMind AI API",
        "status": "running",
    }
