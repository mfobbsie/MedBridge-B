"""
Features router — Mary's full feature list:
- Reminders (CRUD + complete)
- Trusted Contacts (CRUD)
- Follow-ups (CRUD + complete)
- Providers (CRUD)
- Resources / Discover (read-only)
- Health Scores (get + AI generate)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.schemas.errors import GENERIC_INTERNAL_ERROR_MESSAGE
from app.schemas.features import (
    ReminderCreate, ReminderUpdate, ReminderResponse,
    TrustedContactCreate, TrustedContactUpdate, TrustedContactResponse,
    FollowUpCreate, FollowUpUpdate, FollowUpResponse,
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ResourceResponse, HealthScoreResponse,
)
from app.utils.validation import OptionalNonEmptyStr, UuidStr
import logging
import uuid
from datetime import datetime, timezone

router = APIRouter(tags=["Features"])
logger = logging.getLogger(__name__)


def _safe_500(context: str, exc: Exception) -> HTTPException:
    logger.exception("%s: %s", context, exc)
    return HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)


# ══════════════════════════════════════════════════════════════════════════════
# REMINDERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/reminders", response_model=list[ReminderResponse])
async def list_reminders(user: dict = Depends(get_current_user)):
    """List all reminders for the current user, ordered by remind_at."""
    supabase = get_supabase()
    try:
        result = (
            supabase.table("reminders")
            .select("*")
            .eq("user_id", user["id"])
            .order("remind_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        raise _safe_500("Failed to list reminders", e)


@router.post("/reminders", response_model=ReminderResponse, status_code=201)
async def create_reminder(
    payload: ReminderCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new reminder."""
    supabase = get_supabase()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "reminder_type": payload.reminder_type,
        "title": payload.title,
        "body": payload.body,
        "remind_at": payload.remind_at.isoformat(),
        "repeat_interval": payload.repeat_interval,
        "completed": False,
    }
    if payload.health_record_id:
        row["health_record_id"] = payload.health_record_id

    try:
        result = supabase.table("reminders").insert(row).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to create reminder", e)


@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UuidStr,
    payload: ReminderUpdate,
    user: dict = Depends(get_current_user),
):
    """Update a reminder."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("reminders")
            .select("id")
            .eq("id", reminder_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup reminder", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    if "remind_at" in updates:
        updates["remind_at"] = updates["remind_at"].isoformat()

    try:
        result = supabase.table("reminders").update(updates).eq("id", reminder_id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to update reminder", e)


@router.post("/reminders/{reminder_id}/complete", status_code=200)
async def complete_reminder(
    reminder_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Mark a reminder as completed."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("reminders")
            .select("id")
            .eq("id", reminder_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup reminder", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    try:
        supabase.table("reminders").update({"completed": True}).eq("id", reminder_id).execute()
    except Exception as e:
        raise _safe_500("Failed to complete reminder", e)
    return {"reminder_id": reminder_id, "completed": True}


@router.delete("/reminders/{reminder_id}", status_code=204)
async def delete_reminder(
    reminder_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Delete a reminder."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("reminders")
            .select("id")
            .eq("id", reminder_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup reminder", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    try:
        supabase.table("reminders").delete().eq("id", reminder_id).execute()
    except Exception as e:
        raise _safe_500("Failed to delete reminder", e)


# ══════════════════════════════════════════════════════════════════════════════
# TRUSTED CONTACTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/trusted-contacts", response_model=list[TrustedContactResponse])
async def list_trusted_contacts(user: dict = Depends(get_current_user)):
    """List all trusted contacts for the current user."""
    supabase = get_supabase()
    try:
        result = (
            supabase.table("trusted_contacts")
            .select("*")
            .eq("user_id", user["id"])
            .order("created_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        raise _safe_500("Failed to list trusted contacts", e)


@router.post("/trusted-contacts", response_model=TrustedContactResponse, status_code=201)
async def add_trusted_contact(
    payload: TrustedContactCreate,
    user: dict = Depends(get_current_user),
):
    """Add a trusted contact / caregiver."""
    supabase = get_supabase()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "contact_email": payload.contact_email,
        "contact_name": payload.contact_name,
        "access_level": payload.access_level,
        "status": "pending",
    }
    try:
        result = supabase.table("trusted_contacts").insert(row).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to add trusted contact", e)


@router.patch("/trusted-contacts/{contact_id}", response_model=TrustedContactResponse)
async def update_trusted_contact(
    contact_id: UuidStr,
    payload: TrustedContactUpdate,
    user: dict = Depends(get_current_user),
):
    """Update a trusted contact (access level, status, name)."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("trusted_contacts")
            .select("id")
            .eq("id", contact_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup trusted contact", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Trusted contact not found.")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    try:
        result = supabase.table("trusted_contacts").update(updates).eq("id", contact_id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to update trusted contact", e)


@router.delete("/trusted-contacts/{contact_id}", status_code=204)
async def remove_trusted_contact(
    contact_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Remove a trusted contact."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("trusted_contacts")
            .select("id")
            .eq("id", contact_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup trusted contact", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Trusted contact not found.")
    try:
        supabase.table("trusted_contacts").delete().eq("id", contact_id).execute()
    except Exception as e:
        raise _safe_500("Failed to delete trusted contact", e)


# ══════════════════════════════════════════════════════════════════════════════
# FOLLOW-UPS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/documents/{document_id}/follow-ups", response_model=list[FollowUpResponse])
async def list_follow_ups(
    document_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """List all follow-ups for a document."""
    supabase = get_supabase()
    try:
        result = (
            supabase.table("follow_ups")
            .select("*")
            .eq("health_record_id", document_id)
            .eq("user_id", user["id"])
            .order("due_date")
            .execute()
        )
        return result.data or []
    except Exception as e:
        raise _safe_500("Failed to list follow-ups", e)


@router.post("/documents/{document_id}/follow-ups", response_model=FollowUpResponse, status_code=201)
async def create_follow_up(
    document_id: UuidStr,
    payload: FollowUpCreate,
    user: dict = Depends(get_current_user),
):
    """Create a follow-up action item for a document."""
    supabase = get_supabase()
    row = {
        "id": str(uuid.uuid4()),
        "health_record_id": document_id,
        "user_id": user["id"],
        "what": payload.what,
        "when_text": payload.when_text,
        "due_date": payload.due_date.isoformat() if payload.due_date else None,
        "completed": False,
    }
    try:
        result = supabase.table("follow_ups").insert(row).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to create follow-up", e)


@router.patch("/follow-ups/{followup_id}", response_model=FollowUpResponse)
async def update_follow_up(
    followup_id: UuidStr,
    payload: FollowUpUpdate,
    user: dict = Depends(get_current_user),
):
    """Update a follow-up."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("follow_ups")
            .select("id")
            .eq("id", followup_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup follow-up", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Follow-up not found.")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    if "due_date" in updates and updates["due_date"]:
        updates["due_date"] = updates["due_date"].isoformat()

    try:
        result = supabase.table("follow_ups").update(updates).eq("id", followup_id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to update follow-up", e)


@router.post("/follow-ups/{followup_id}/complete", status_code=200)
async def complete_follow_up(
    followup_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Mark a follow-up as completed."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("follow_ups")
            .select("id")
            .eq("id", followup_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup follow-up", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Follow-up not found.")
    try:
        supabase.table("follow_ups").update({"completed": True}).eq("id", followup_id).execute()
    except Exception as e:
        raise _safe_500("Failed to complete follow-up", e)
    return {"followup_id": followup_id, "completed": True}


@router.delete("/follow-ups/{followup_id}", status_code=204)
async def delete_follow_up(
    followup_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Delete a follow-up."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("follow_ups")
            .select("id")
            .eq("id", followup_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup follow-up", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Follow-up not found.")
    try:
        supabase.table("follow_ups").delete().eq("id", followup_id).execute()
    except Exception as e:
        raise _safe_500("Failed to delete follow-up", e)


# ══════════════════════════════════════════════════════════════════════════════
# PROVIDERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(user: dict = Depends(get_current_user)):
    """List the patient's care team providers."""
    supabase = get_supabase()
    try:
        result = (
            supabase.table("providers")
            .select("*")
            .eq("user_id", user["id"])
            .order("name")
            .execute()
        )
        return result.data or []
    except Exception as e:
        raise _safe_500("Failed to list providers", e)


@router.post("/providers", response_model=ProviderResponse, status_code=201)
async def add_provider(
    payload: ProviderCreate,
    user: dict = Depends(get_current_user),
):
    """Add a provider to the patient's care team."""
    supabase = get_supabase()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": payload.name,
        "specialty": payload.specialty,
        "phone": payload.phone,
        "address": payload.address,
        "fhir_provider_id": payload.fhir_provider_id,
    }
    try:
        result = supabase.table("providers").insert(row).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to add provider", e)


@router.patch("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UuidStr,
    payload: ProviderUpdate,
    user: dict = Depends(get_current_user),
):
    """Update a provider."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("providers")
            .select("id")
            .eq("id", provider_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup provider", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Provider not found.")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    try:
        result = supabase.table("providers").update(updates).eq("id", provider_id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise _safe_500("Failed to update provider", e)


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Remove a provider from the care team."""
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("providers")
            .select("id")
            .eq("id", provider_id)
            .eq("user_id", user["id"])
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to lookup provider", e)

    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="Provider not found.")
    try:
        supabase.table("providers").delete().eq("id", provider_id).execute()
    except Exception as e:
        raise _safe_500("Failed to delete provider", e)


# ══════════════════════════════════════════════════════════════════════════════
# RESOURCES / DISCOVER
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    resource_type: OptionalNonEmptyStr = Query(None),
    tag: OptionalNonEmptyStr = Query(None),
    user: dict = Depends(get_current_user),
):
    """
    Browse health resources (Discover section).
    Optional filters: resource_type, tag.
    Resources are shared — not per-user.
    """
    supabase = get_supabase()
    try:
        query = supabase.table("resources").select("*")
        if resource_type:
            query = query.eq("resource_type", resource_type)
        result = query.order("title").execute()

        rows = result.data or []
        if tag:
            rows = [r for r in rows if r.get("tags") and tag in r["tags"]]
        return rows
    except Exception as e:
        raise _safe_500("Failed to list resources", e)


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """Get a single resource."""
    supabase = get_supabase()
    try:
        result = (
            supabase.table("resources")
            .select("*")
            .eq("id", resource_id)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise _safe_500("Failed to get resource", e)

    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return result.data


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH SCORES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/health-scores", response_model=list[HealthScoreResponse])
async def list_health_scores(user: dict = Depends(get_current_user)):
    """List all health scores for the current user, most recent first."""
    supabase = get_supabase()
    try:
        result = (
            supabase.table("health_scores")
            .select("*")
            .eq("user_id", user["id"])
            .order("scored_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        raise _safe_500("Failed to list health scores", e)


@router.post("/documents/{document_id}/health-score", response_model=HealthScoreResponse, status_code=201)
async def generate_health_score(
    document_id: UuidStr,
    user: dict = Depends(get_current_user),
):
    """
    Generate a health engagement score from a document using AI.
    Scores how well the patient is keeping up with their care plan.
    Scale: 0-100. Label: Excellent / Good / Needs Attention / Critical.
    """
    supabase = get_supabase()
    from app.services import document_service
    doc = document_service.get_document(document_id, user["id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.get("status") != "summarized":
        raise HTTPException(status_code=400, detail="Document still processing.")

    extracted_text = doc.get("extracted_text") or doc.get("raw_text", "")
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Document text not available.")

    from app.services.health_score_service import generate_health_score as compute_score
    result = compute_score(extracted_text)
    if not result.get("success"):
        logger.error("Health score generation failed for document %s", document_id)
        raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)

    score_id = str(uuid.uuid4())
    row = {
        "id": score_id,
        "user_id": user["id"],
        "health_record_id": document_id,
        "score": result["score"],
        "score_label": result["label"],
        "rationale": result["rationale"],
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("health_scores").insert(row).execute()
    except Exception as e:
        raise _safe_500("Failed to store health score", e)

    return {**row, "created_at": row["scored_at"]}
