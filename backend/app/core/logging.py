"""
Production logging configuration for the ResearchMind AI platform.

Uses structlog for structured, JSON-formatted log output when running
in production (APP_ENV=production) or pretty-printed console output in
development.
"""

import logging
import sys

import structlog


def setup_logging(env: str = "development") -> None:
    """
    Configure structured logging for the application.

    Parameters
    ----------
    env : str
        The runtime environment.  When ``"production"``, log output
        is JSON-formatted for ingestion by log aggregators.  In any
        other environment, human-friendly console output is used.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if env == "production":
        # JSON-formatted logs for production (log aggregators)
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty-printed console output for development
        processors = [
            *shared_processors,
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure the root stdlib logger so third-party libraries use
    # structlog's formatting.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Suppress noisy third-party loggers in production
    if env == "production":
        for logger_name in ("uvicorn.access", "httpx"):
            logging.getLogger(logger_name).setLevel(logging.WARNING)
