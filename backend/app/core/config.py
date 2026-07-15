from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-level settings loaded from environment variables / .env file."""

    # -- App metadata -----------------------------------------------------------
    APP_NAME: str = "ResearchMind AI"
    APP_VERSION: str = "0.1.0"

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

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Return a singleton Settings instance (cached for the lifetime of the process)."""
    return Settings()


settings = get_settings()
