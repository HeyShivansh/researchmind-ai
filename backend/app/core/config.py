from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env")

    # -- App metadata -----------------------------------------------------------
    APP_NAME: str = "ResearchMind AI"
    APP_VERSION: str = "1.0.0"

    # -- Runtime ----------------------------------------------------------------
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -- PostgreSQL -------------------------------------------------------------
    POSTGRES_USER: str = "researchmind"
    POSTGRES_PASSWORD: str = "researchmind"
    POSTGRES_DB: str = "researchmind"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        """Build the synchronous PostgreSQL connection string."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # -- Connection pooling defaults --------------------------------------------
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_ECHO: bool = False

    # -- Storage -----------------------------------------------------------------
    STORAGE_ROOT: str = "storage"
    PAPERS_DIRECTORY: str = "papers"
    MAX_UPLOAD_SIZE_MB: int = 50

    # -- Chunking ----------------------------------------------------------------
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50

    # -- Embeddings --------------------------------------------------------------
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # -- Vector store (Qdrant) ---------------------------------------------------
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "researchmind"
    QDRANT_VECTOR_DIMENSION: int = 768

    # -- Hybrid retrieval --------------------------------------------------------
    HYBRID_SEMANTIC_TOP_K: int = 10
    HYBRID_KEYWORD_TOP_K: int = 10
    HYBRID_FUSION_K: int = 60

    # -- CORS ---------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000"

    # -- JWT / Authentication -----------------------------------------------------
    SECRET_KEY: str = "change-me-to-a-secure-random-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


@lru_cache
def get_settings() -> Settings:
    """Return a singleton Settings instance (cached for the lifetime of the process)."""
    return Settings()


settings = get_settings()
