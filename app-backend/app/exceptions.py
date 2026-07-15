"""Global exception handlers and custom HTTP exceptions."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.errors import (
    GENERIC_INTERNAL_ERROR_MESSAGE,
    STATUS_TO_ERROR_CODE,
    ApiErrorResponse,
    ValidationDetail,
)

logger = logging.getLogger(__name__)


class MedBridgeHTTPException(HTTPException):
    """HTTPException with optional structured error metadata."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        *,
        error_code: str | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.retry_after = retry_after


def _normalize_detail(detail: Any) -> tuple[str, list[ValidationDetail] | None]:
    if isinstance(detail, list):
        details = [
            ValidationDetail(
                field=".".join(
                    str(part) for part in item.get("loc", []) if part not in ("body", "query", "path")
                )
                or "request",
                message=item.get("msg", ""),
                type=item.get("type", ""),
            )
            for item in detail
            if isinstance(item, dict)
        ]
        return "Request validation failed", details or None

    if isinstance(detail, str):
        return detail, None

    return str(detail), None


def _build_error_response(
    status_code: int,
    detail: Any,
    *,
    error_code: str | None = None,
    retry_after: int | None = None,
) -> JSONResponse:
    message, details = _normalize_detail(detail)
    body = ApiErrorResponse(
        error_code=error_code or STATUS_TO_ERROR_CODE.get(status_code, "INTERNAL_ERROR"),
        message=message,
        details=details,
        retry_after=retry_after,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MedBridgeHTTPException)
    async def medbridge_http_exception_handler(
        request: Request,
        exc: MedBridgeHTTPException,
    ) -> JSONResponse:
        return _build_error_response(
            exc.status_code,
            exc.detail,
            error_code=exc.error_code,
            retry_after=exc.retry_after,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _build_error_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            ValidationDetail(
                field=".".join(
                    str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path")
                )
                or "request",
                message=err.get("msg", ""),
                type=err.get("type", ""),
            )
            for err in exc.errors()
        ]
        body = ApiErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        body = ApiErrorResponse(
            error_code="INTERNAL_ERROR",
            message=GENERIC_INTERNAL_ERROR_MESSAGE,
        )
        return JSONResponse(status_code=500, content=body.model_dump())
