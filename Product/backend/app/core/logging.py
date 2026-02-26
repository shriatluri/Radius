"""
Structured JSON logging for Radius.

Every log line is a JSON object — machine-parseable, queryable, audit-friendly.

Two pieces of context are automatically injected into every log line:
  - request_id: unique ID per HTTP request (set by RequestIdMiddleware)
  - business_id: the authenticated tenant (set by API endpoints before service calls)

These use Python's contextvars — like thread-local storage but safe for async code.
Each concurrent request gets its own isolated values, so they never bleed across requests.

Usage:
    from app.core.logging import set_business_id
    set_business_id(auth.business_id)  # call this in API endpoints

    import logging
    logger = logging.getLogger(__name__)
    logger.info("sanctions_check", extra={"wallet": wallet, "result": "passed"})
"""

import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

# ---------------------------------------------------------------------------
# Context variables — one value per running request, isolated across requests
# ---------------------------------------------------------------------------
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_business_id_var: ContextVar[str] = ContextVar("business_id", default="")


def get_request_id() -> str:
    return _request_id_var.get()


def set_request_id(value: str) -> None:
    _request_id_var.set(value)


def get_business_id() -> str:
    return _business_id_var.get()


def set_business_id(value: str) -> None:
    _business_id_var.set(value)


# ---------------------------------------------------------------------------
# Log filter — runs on every log record and injects context into it
# ---------------------------------------------------------------------------
class _RequestContextFilter(logging.Filter):
    """Stamps every log record with the current request_id and business_id."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()  # type: ignore[attr-defined]
        record.business_id = get_business_id()  # type: ignore[attr-defined]
        return True


# ---------------------------------------------------------------------------
# Setup — call once at application startup
# ---------------------------------------------------------------------------
def setup_logging() -> None:
    """
    Replace the default Python logger with a JSON-structured one.

    Output format (one JSON object per line):
    {
      "timestamp": "2026-02-26T14:32:01Z",
      "level": "INFO",
      "logger": "app.services.risk",
      "request_id": "req_a3f9c2",
      "business_id": "acme_corp",
      "message": "risk_scored",
      "score": 15,
      "level_name": "low"
    }
    """
    handler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(business_id)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    handler.addFilter(_RequestContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
