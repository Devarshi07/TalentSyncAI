"""
Structured logging for production.
"""
import logging
import sys
from typing import Any


def setup_logging(debug: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    # Reduce noise from third-party libs
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING
    )  # Disable request logging in prod (use middleware if needed)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    request_id: str | None = None,
    user_id: str | None = None,
) -> None:
    extra: dict[str, Any] = {
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id
    logger.info("Request completed", extra=extra)
