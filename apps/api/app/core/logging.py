"""Structured logging configuration for AI Coding Gym API."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONLogFormatter(logging.Formatter):
    """Custom JSON formatter for structured application logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include exception details if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include structured extra attributes if provided
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logging(debug: bool = False) -> None:
    """Initialize structured logging for stdout."""
    log_level = logging.DEBUG if debug else logging.INFO

    # Remove all existing handlers from the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)

    if debug:
        # Development human-readable format
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Production structured JSON format
        formatter = JSONLogFormatter()

    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Suppress overly noisy third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
