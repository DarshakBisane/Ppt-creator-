"""Structured logging configuration."""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

import re

# Context variable to hold request ID for logging correlation
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[_-]?key|auth|authorization|password|secret|token|bearer)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(AIza[0-9A-Za-z-_]{35}|Bearer\s+[A-Za-z0-9\-_=.]+)",
    re.IGNORECASE,
)

IGNORED_LOG_RECORD_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName",
}


def sanitize_log_value(val: Any) -> Any:
    """Sanitize any potentially sensitive values in log payloads."""
    if isinstance(val, str):
        return SENSITIVE_VALUE_PATTERN.sub("[REDACTED]", val)
    if isinstance(val, dict):
        sanitized: dict[str, Any] = {}
        for k, v in val.items():
            if SENSITIVE_KEY_PATTERN.search(str(k)):
                sanitized[str(k)] = "[REDACTED]"
            else:
                sanitized[str(k)] = sanitize_log_value(v)
        return sanitized
    if isinstance(val, list):
        return [sanitize_log_value(item) for item in val]
    return val


class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as structured, secret-safe JSON."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        raw_msg = record.getMessage()
        safe_msg = SENSITIVE_VALUE_PATTERN.sub("[REDACTED]", raw_msg)

        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": safe_msg,
        }

        if req_id:
            log_payload["request_id"] = req_id

        # Include custom extra fields
        for key, val in record.__dict__.items():
            if key not in IGNORED_LOG_RECORD_ATTRS and not key.startswith("_"):
                if SENSITIVE_KEY_PATTERN.search(key):
                    log_payload[key] = "[REDACTED]"
                else:
                    log_payload[key] = sanitize_log_value(val)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


class StructuredTextFormatter(logging.Formatter):
    """Clean human-readable formatter for local development with secret redaction."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        req_part = f" [{req_id}]" if req_id else ""
        time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        raw_msg = record.getMessage()
        safe_msg = SENSITIVE_VALUE_PATTERN.sub("[REDACTED]", raw_msg)

        # Collect extra fields
        extras = []
        for key, val in record.__dict__.items():
            if key not in IGNORED_LOG_RECORD_ATTRS and not key.startswith("_"):
                safe_v = "[REDACTED]" if SENSITIVE_KEY_PATTERN.search(key) else sanitize_log_value(val)
                extras.append(f"{key}={safe_v}")

        extra_part = f" ({', '.join(extras)})" if extras else ""
        res = f"{time_str} | {record.levelname:<8} | {record.name}{req_part} - {safe_msg}{extra_part}"
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

