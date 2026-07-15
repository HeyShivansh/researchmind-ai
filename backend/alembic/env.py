"""
Alembic environment configuration for ResearchMind AI.

This module is loaded by the ``alembic`` CLI every time a migration command
is run.  It is *not* part of the FastAPI application itself.

Key responsibilities:

* Load the database URL from the application Settings object so there is a
  single source of truth for configuration (``app.core.config``).
* Register every ORM model via the ``app.models`` package so that Alembic's
  autogenerate feature can compare the model metadata against the current
  database schema.
* Provide both online (live database) and offline (SQL script) runners.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Logging — wire up the loggers defined in alembic.ini
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Model metadata
# ---------------------------------------------------------------------------
# Import all models so their ``__tablename__`` tables are registered on
# ``Base.metadata``.  Alembic autogenerate uses ``target_metadata`` to detect
# differences between the current schema and the model definitions.
# ---------------------------------------------------------------------------
from app.database.base import Base  # noqa: E402
import app.models  # noqa: E402  registers every ORM model with Base.metadata

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override the database URL with the value from application settings
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# ---------------------------------------------------------------------------
# Offline runner — emit SQL statements to a file / stdout
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without connecting to a database.

    The generated SQL script can be reviewed and applied later by a DBA or
    a CI/CD pipeline.
    """
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Instruct Alembic to use SQLAlchemy 2.0 render style
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online runner — apply migrations directly against the live database
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations in 'online' mode against the live PostgreSQL database.

    Creates a dedicated engine (with a NullPool so connections are not
    held open after the migration finishes) and runs all pending revisions
    within a single transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point — Alembic invokes the correct runner based on the CLI flags
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
