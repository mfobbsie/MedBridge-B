from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import logging

from app.database import get_supabase
from app.middleware.auth import get_current_user
from app.schemas.errors import GENERIC_INTERNAL_ERROR_MESSAGE

router = APIRouter(prefix="/user-settings", tags=["user_settings"])
logger = logging.getLogger(__name__)


class UserSettingsUpdate(BaseModel):
    allow_trusted_contacts: Optional[bool] = None
    allow_mychart_integration: Optional[bool] = None
    enable_reminders: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    allow_trusted_contacts: bool
    allow_mychart_integration: bool
    enable_reminders: bool
    updated_at: datetime


@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(user: dict = Depends(get_current_user)):
    db = get_supabase()
    try:
        result = db.table("user_settings").select("*").eq("user_id", user["id"]).execute()

        if not result.data:
            result = db.table("user_settings").insert({"user_id": user["id"]}).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=GENERIC_INTERNAL_ERROR_MESSAGE,
            )
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get user settings: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=GENERIC_INTERNAL_ERROR_MESSAGE,
        )


@router.patch("/", response_model=UserSettingsResponse)
async def update_user_settings(
    payload: UserSettingsUpdate,
    user: dict = Depends(get_current_user),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    db = get_supabase()
    try:
        result = (
            db.table("user_settings")
            .update(updates)
            .eq("user_id", user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Settings not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update user settings: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=GENERIC_INTERNAL_ERROR_MESSAGE,
        )
