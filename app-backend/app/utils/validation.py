"""Shared Pydantic/FastAPI validation helpers for MedBridge APIs."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Optional, TypeVar

from pydantic import AfterValidator, BeforeValidator, Field

T = TypeVar("T")


def _trim_str(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def _require_non_empty(value: str) -> str:
    if not value:
        raise ValueError("must not be empty")
    return value


def _optional_non_empty(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("must not be empty")
        return trimmed
    return value


def _parse_uuid(value: Any) -> str:
    """Accept UUID objects or UUID strings; return canonical string form."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, str):
        trimmed = value.strip()
        try:
            return str(uuid.UUID(trimmed))
        except ValueError as exc:
            raise ValueError("must be a valid UUID") from exc
    raise ValueError("must be a valid UUID")


# Non-empty trimmed string (required fields)
NonEmptyStr = Annotated[
    str,
    BeforeValidator(_trim_str),
    AfterValidator(_require_non_empty),
]

# Optional non-empty trimmed string (rejects "", "   ")
OptionalNonEmptyStr = Annotated[
    Optional[str],
    BeforeValidator(lambda v: _trim_str(v) if isinstance(v, str) else v),
    AfterValidator(_optional_non_empty),
]

# UUID path/body ID as string
UuidStr = Annotated[str, BeforeValidator(_parse_uuid)]


def reject_empty_update(updates: dict) -> None:
    """Raise ValueError if a PATCH payload produced no fields to update.

    Callers should convert this into HTTP 400.
    """
    if not updates:
        raise ValueError("No fields provided to update.")


def fields_set_or_raise(model: Any, *, exclude: set[str] | None = None) -> dict:
    """Return dumped fields that were explicitly set, excluding Nones.

    Raises ValueError when the resulting update dict is empty.
    """
    exclude = exclude or set()
    data = model.model_dump(exclude_unset=True)
    updates = {
        k: v
        for k, v in data.items()
        if k not in exclude and v is not None
    }
    reject_empty_update(updates)
    return updates
