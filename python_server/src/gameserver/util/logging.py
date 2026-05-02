"""Structured logging configuration (structlog).

Call ``configure_logging()`` once at process startup (in ``main.py`` and
``fastapi_server.py``) before any logger is used.

Usage elsewhere::

    import structlog
    log = structlog.get_logger(__name__)
    log.info("empire_built", uid=42, iid="BASIC_TOWER")

Environment variable:
    LOG_FORMAT=json      → JSON lines (default in production)
    LOG_FORMAT=console   → human-readable coloured output (default in dev)
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys

import structlog


def configure_logging(
    log_file: str | None = None,
    level: int = logging.INFO,
) -> None:
    """Wire structlog + stdlib logging.

    Args:
        log_file: Path for the rotating file handler.  ``None`` = stdout only.
        level:    Root log level.
    """
    fmt = os.environ.get("LOG_FORMAT", "console").lower()
    use_json = fmt == "json"

    # --- shared processors (both renderers) --------------------------------
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if use_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processor=renderer,
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Remove any handlers added before configure_logging() is called
    root.handlers.clear()

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    if log_file:
        fh = logging.handlers.TimedRotatingFileHandler(
            log_file, when="midnight", backupCount=14, utc=True, encoding="utf-8"
        )
        fh.setFormatter(formatter)
        root.addHandler(fh)

    # Quiet noisy third-party loggers
    logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
