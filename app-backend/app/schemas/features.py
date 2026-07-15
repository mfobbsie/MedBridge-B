"""
Pydantic schemas for Mary features:
reminders, trusted_contacts, follow_ups, providers, resources, health_scores
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from datetime import datetime, date

from app.utils.validation import NonEmptyStr, OptionalNonEmptyStr, UuidStr


ReminderType = Literal["medication", "appointment", "follow_up", "general"]
RepeatInterval = Literal["daily", "weekly", "monthly"]
AccessLevel = Literal["read", "full"]
ContactStatus = Literal["pending", "accepted", "revoked"]


# ── Reminders ────────────────────────────────────────────────────────────────

class ReminderCreate(BaseModel):
    health_record_id: Optional[UuidStr] = None
    reminder_type: ReminderType
    title: NonEmptyStr = Field(..., min_length=1, max_length=255)
    body: OptionalNonEmptyStr = None
    remind_at: datetime
    repeat_interval: Optional[RepeatInterval] = None

class ReminderUpdate(BaseModel):
    title: OptionalNonEmptyStr = Field(None, min_length=1, max_length=255)
    body: OptionalNonEmptyStr = None
    remind_at: Optional[datetime] = None
    repeat_interval: Optional[RepeatInterval] = None
    completed: Optional[bool] = None

class ReminderResponse(BaseModel):
    id: str
    user_id: str
    health_record_id: Optional[str] = None
    reminder_type: str
    title: str
    body: Optional[str] = None
    remind_at: datetime
    repeat_interval: Optional[str] = None
    completed: bool
    created_at: datetime


# ── Trusted Contacts ─────────────────────────────────────────────────────────

class TrustedContactCreate(BaseModel):
    contact_email: EmailStr
    contact_name: NonEmptyStr = Field(..., min_length=1, max_length=255)
    access_level: AccessLevel = "read"

class TrustedContactUpdate(BaseModel):
    contact_name: OptionalNonEmptyStr = Field(None, min_length=1, max_length=255)
    access_level: Optional[AccessLevel] = None
    status: Optional[ContactStatus] = None

class TrustedContactResponse(BaseModel):
    id: str
    user_id: str
    contact_email: str
    contact_name: str
    access_level: str
    status: str
    created_at: datetime


# ── Follow-ups ───────────────────────────────────────────────────────────────

class FollowUpCreate(BaseModel):
    what: NonEmptyStr = Field(..., min_length=1, max_length=1000)
    when_text: OptionalNonEmptyStr = None
    due_date: Optional[date] = None

class FollowUpUpdate(BaseModel):
    what: OptionalNonEmptyStr = Field(None, min_length=1, max_length=1000)
    when_text: OptionalNonEmptyStr = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None

class FollowUpResponse(BaseModel):
    id: str
    health_record_id: str
    user_id: str
    what: str
    when_text: Optional[str] = None
    due_date: Optional[date] = None
    completed: bool
    created_at: datetime


# ── Providers ────────────────────────────────────────────────────────────────

class ProviderCreate(BaseModel):
    name: NonEmptyStr = Field(..., min_length=1, max_length=255)
    specialty: OptionalNonEmptyStr = None
    phone: OptionalNonEmptyStr = None
    address: OptionalNonEmptyStr = None
    fhir_provider_id: OptionalNonEmptyStr = None

class ProviderUpdate(BaseModel):
    name: OptionalNonEmptyStr = Field(None, min_length=1, max_length=255)
    specialty: OptionalNonEmptyStr = None
    phone: OptionalNonEmptyStr = None
    address: OptionalNonEmptyStr = None

class ProviderResponse(BaseModel):
    id: str
    user_id: str
    name: str
    specialty: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    fhir_provider_id: Optional[str] = None
    created_at: datetime


# ── Resources (Discover) ─────────────────────────────────────────────────────

class ResourceResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    resource_type: Optional[str] = None
    tags: Optional[list] = None
    condition_codes: Optional[list] = None
    created_at: datetime


# ── Health Scores ─────────────────────────────────────────────────────────────

class HealthScoreResponse(BaseModel):
    id: str
    user_id: str
    health_record_id: Optional[str] = None
    score: float
    score_label: Optional[str] = None
    rationale: Optional[str] = None
    scored_at: datetime
    created_at: datetime
