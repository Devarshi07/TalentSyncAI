"""
Centralized error handling for production.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .logging import get_logger

logger = get_logger(__name__)


def _make_serializable(obj):
    """Recursively convert non-serializable objects to strings."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors without exposing internals."""
    errors = _make_serializable(exc.errors())
    logger.warning("Validation error", extra={"errors": errors})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected errors - never expose stack traces in production."""
    import config
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled exception",
        extra={"request_id": request_id, "path": request.url.path},
    )
    detail = "An unexpected error occurred"
    if config.DEBUG:
        detail = str(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "request_id": request_id,
        },
    )
