"""Unit tests for patient profile request/response schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.patient_profile import PatientProfileCreate, PatientProfileUpdate


def test_create_requires_full_name_and_language():
    profile = PatientProfileCreate(
        full_name="Jane Doe",
        preferred_language="en",
    )
    assert profile.explanation_level == "plain"


def test_create_rejects_invalid_explanation_level():
    with pytest.raises(ValidationError):
        PatientProfileCreate(
            full_name="Jane Doe",
            preferred_language="en",
            explanation_level="verbose",
        )


def test_update_allows_partial_fields():
    profile = PatientProfileUpdate(full_name="Updated Name")
    assert profile.preferred_language is None
    assert profile.explanation_level is None
