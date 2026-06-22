"""
Structured JSON logging setup.
"""
import logging
import sys
from typing import Optional

import structlog


def setup_logging(level: Optional[str] = None) -> None:
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if _is_dev() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )


def _is_dev() -> bool:
    import os
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
