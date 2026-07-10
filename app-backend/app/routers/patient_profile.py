"""
Patient health profile router.

Endpoints:
  POST  /patient-profile  — create or complete a profile
  GET   /patient-profile  — retrieve the logged-in user's profile
  PATCH /patient-profile  — update profile fields
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_supabase
from app.middleware.auth import get_current_user
from app.schemas.patient_profile import (
    PatientProfileCreate,
    PatientProfileResponse,
    PatientProfileUpdate,
)

router = APIRouter(prefix="/patient-profile", tags=["Patient Profile"])


def _to_response(row: dict, email: str) -> PatientProfileResponse:
    return PatientProfileResponse(
        user_id=row["user_id"],
        email=email,
        full_name=row.get("full_name"),
        preferred_language=row.get("preferred_language", "en"),
        explanation_level=row.get("explanation_level", "plain"),
    )


def _get_profile_row(supabase, user_id: str) -> dict | None:
    result = (
        supabase.table("user_profiles")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return result.data


@router.post("", response_model=PatientProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_profile(
    payload: PatientProfileCreate,
    user: dict = Depends(get_current_user),
):
    """
    Create a health profile for the authenticated user.

    Registration may insert a stub row with only `user_id`; in that case this
    endpoint completes the profile. Returns 409 if a profile with `full_name`
    already exists.
    """
    supabase = get_supabase()
    existing = _get_profile_row(supabase, user["id"])

    row_data = {
        "full_name": payload.full_name,
        "preferred_language": payload.preferred_language,
        "explanation_level": payload.explanation_level,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if existing is None:
        row_data["user_id"] = user["id"]
        result = supabase.table("user_profiles").insert(row_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create patient profile.")
        return _to_response(result.data[0], user["email"])

    if existing.get("full_name"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient profile already exists. Use PATCH to update.",
        )

    result = (
        supabase.table("user_profiles")
        .update(row_data)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create patient profile.")
    return _to_response(result.data[0], user["email"])


@router.get("", response_model=PatientProfileResponse)
async def get_patient_profile(user: dict = Depends(get_current_user)):
    """Retrieve the authenticated user's health profile."""
    supabase = get_supabase()
    row = _get_profile_row(supabase, user["id"])
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")
    return _to_response(row, user["email"])


@router.patch("", response_model=PatientProfileResponse)
async def update_patient_profile(
    payload: PatientProfileUpdate,
    user: dict = Depends(get_current_user),
):
    """Update the authenticated user's health profile."""
    supabase = get_supabase()
    existing = _get_profile_row(supabase, user["id"])
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update.")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("user_profiles")
        .update(updates)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update patient profile.")
    return _to_response(result.data[0], user["email"])
