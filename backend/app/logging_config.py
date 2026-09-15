"""Structured logging configuration."""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Context variable to hold request ID for logging correlation
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if req_id:
            log_payload["request_id"] = req_id

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


class StructuredTextFormatter(logging.Formatter):
    """Clean human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        req_part = f" [{req_id}]" if req_id else ""
        time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        msg = record.getMessage()
        res = f"{time_str} | {record.levelname:<8} | {record.name}{req_part} - {msg}"
        if record.exc_info:
            res += f"\n{self.formatException(record.exc_info)}"
        return res


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Initialize structured application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = StructuredJsonFormatter() if json_logs else StructuredTextFormatter()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Reduce verbosity of noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
