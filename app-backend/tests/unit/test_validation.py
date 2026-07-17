"""Unit tests for shared validation helpers and schema constraints."""

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.documents import ChatRequest
from app.schemas.features import (
    FollowUpCreate,
    ProviderCreate,
    ReminderCreate,
    TrustedContactCreate,
)
from app.schemas.medications import MedicationCreate, MedicationUpdate
from app.schemas.patient_profile import PatientProfileCreate, PatientProfileUpdate
from app.utils.validation import NonEmptyStr, OptionalNonEmptyStr, UuidStr, reject_empty_update


class _UuidModel(BaseModel):
    id: UuidStr


class _StrModel(BaseModel):
    name: NonEmptyStr
    note: OptionalNonEmptyStr = None


def test_uuid_str_accepts_valid_uuid():
    model = _UuidModel(id="550e8400-e29b-41d4-a716-446655440000")
    assert model.id == "550e8400-e29b-41d4-a716-446655440000"


def test_uuid_str_rejects_invalid_id():
    with pytest.raises(ValidationError):
        _UuidModel(id="not-a-uuid")


def test_non_empty_str_rejects_whitespace():
    with pytest.raises(ValidationError):
        _StrModel(name="   ")


def test_optional_non_empty_str_rejects_blank():
    with pytest.raises(ValidationError):
        _StrModel(name="ok", note="   ")


def test_reject_empty_update():
    with pytest.raises(ValueError, match="No fields"):
        reject_empty_update({})


def test_chat_request_rejects_whitespace_question():
    with pytest.raises(ValidationError):
        ChatRequest(question="   ")


def test_auth_rejects_blank_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="a@b.com", password="   ")
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="        ")


def test_patient_profile_rejects_whitespace_name():
    with pytest.raises(ValidationError):
        PatientProfileCreate(full_name="  ", preferred_language="en")
    with pytest.raises(ValidationError):
        PatientProfileUpdate(full_name="   ")


def test_medication_rejects_whitespace_name():
    with pytest.raises(ValidationError):
        MedicationCreate(name="  ")
    with pytest.raises(ValidationError):
        MedicationUpdate(name="   ")


def test_reminder_rejects_invalid_type_and_empty_title():
    with pytest.raises(ValidationError):
        ReminderCreate(
            reminder_type="invalid",
            title="Take meds",
            remind_at="2026-07-15T10:00:00Z",
        )
    with pytest.raises(ValidationError):
        ReminderCreate(
            reminder_type="medication",
            title="  ",
            remind_at="2026-07-15T10:00:00Z",
        )


def test_trusted_contact_requires_email_and_name():
    with pytest.raises(ValidationError):
        TrustedContactCreate(contact_email="not-an-email", contact_name="Ada")
    with pytest.raises(ValidationError):
        TrustedContactCreate(contact_email="ada@example.com", contact_name="  ")


def test_follow_up_and_provider_reject_empty_required_fields():
    with pytest.raises(ValidationError):
        FollowUpCreate(what="  ")
    with pytest.raises(ValidationError):
        ProviderCreate(name="")
