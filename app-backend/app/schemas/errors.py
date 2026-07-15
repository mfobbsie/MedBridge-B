"""Standard API error response schemas for MedBridge."""

from typing import Literal, Optional

from pydantic import BaseModel

GENERIC_INTERNAL_ERROR_MESSAGE = "An unexpected error occurred. Please try again."

STATUS_TO_ERROR_CODE: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


class ValidationDetail(BaseModel):
    field: str
    message: str
    type: str


class ApiErrorResponse(BaseModel):
    """Standard error response returned by all MedBridge REST API endpoints."""

    success: Literal[False] = False
    error_code: str
    message: str
    details: Optional[list[ValidationDetail]] = None
    retry_after: Optional[int] = None


# Backward-compatible alias used by existing AI error helpers and frontend types.
ErrorEnvelope = ApiErrorResponse


def error_response(
    status_code: int,
    message: str,
    *,
    error_code: str | None = None,
    details: list[ValidationDetail] | None = None,
    retry_after: int | None = None,
) -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code=error_code or STATUS_TO_ERROR_CODE.get(status_code, "INTERNAL_ERROR"),
        message=message,
        details=details,
        retry_after=retry_after,
    )


def groq_timeout_error() -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code="GROQ_TIMEOUT",
        message="The AI is taking longer than usual. Please try again in a moment.",
        retry_after=5,
    )


def groq_unavailable_error() -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code="GROQ_UNAVAILABLE",
        message="The AI service is temporarily unavailable. Please try again shortly.",
        retry_after=10,
    )


def document_not_found_error() -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code="DOC_NOT_FOUND",
        message="We could not find that document. It may have been removed.",
    )


def extraction_failed_error() -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code="EXTRACTION_FAILED",
        message=(
            "We had trouble reading that file. Try uploading a clearer photo "
            "or a different file format."
        ),
    )


def unauthorized_error() -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code="UNAUTHORIZED",
        message="Your session has expired. Please sign in again.",
    )
