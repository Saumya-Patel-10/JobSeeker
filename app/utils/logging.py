"""Structured logging configuration.

Outputs JSON to a rotating file at ``data/logs/app.log`` and a human-friendly
renderer to stderr. Call :func:`configure_logging` once near process start
(the CLI and API entry points do this for you).
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config.paths import LOG_DIR

_configured: bool = False


def _add_app_context(
    _logger: logging.Logger, _method_name: str, event_dict: EventDict
) -> EventDict:
    event_dict.setdefault("app", "jobassist")
    return event_dict


def _build_shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _add_app_context,
    ]


def configure_logging(
    level: str | None = None,
    *,
    log_file: str = "app.log",
    json_console: bool = False,
) -> None:
    """Configure structlog and the stdlib logging system.

    Args:
        level: Log level name. Falls back to ``JOBASSIST_LOG_LEVEL`` env var
            or ``INFO``.
        log_file: File under ``data/logs/`` to write JSON logs to.
        json_console: If True, emit JSON to stderr instead of the colored
            console renderer. Useful when piping logs into ``jq``.
    """
    global _configured
    if _configured:
        return

    resolved_level = (level or os.environ.get("JOBASSIST_LOG_LEVEL", "INFO")).upper()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_path = LOG_DIR / log_file

    shared_processors = _build_shared_processors()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    json_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processor=structlog.processors.JSONRenderer(),
    )
    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processor=(
            structlog.processors.JSONRenderer()
            if json_console
            else structlog.dev.ConsoleRenderer(colors=True)
        ),
    )

    file_handler = logging.handlers.RotatingFileHandler(
        file_path, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(json_formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(console_formatter)

    root = logging.getLogger()
    root.setLevel(resolved_level)
    root.handlers = [file_handler, console_handler]

    for noisy in ("httpx", "httpcore", "urllib3", "asyncio", "chromadb", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger bound to ``name`` (defaults to module name)."""
    return structlog.get_logger(name)
