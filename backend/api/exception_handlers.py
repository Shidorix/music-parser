"""FastAPI exception handlers that preserve the API response envelope."""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.core.exceptions import AppException
from backend.schemas import APIError, APIResponse

logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Return expected business errors in the standard envelope."""
    logger.info(
        "Application error on %s %s: %s",
        request.method,
        request.url.path,
        exc.code,
    )
    return _build_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return request validation errors in the standard envelope."""
    logger.info(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return _build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return unexpected errors in the standard envelope."""
    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="Unexpected internal server error.",
    )


def _build_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    payload = APIResponse[None](
        data=None,
        meta=None,
        error=APIError(code=code, message=message),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )
