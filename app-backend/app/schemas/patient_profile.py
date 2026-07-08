"""
Pydantic schemas for the patient health profile API.

Response shape matches app-frontend/src/types/auth.ts UserProfile.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


ExplanationLevel = Literal["plain", "detailed"]


class PatientProfileCreate(BaseModel):
    full_name: str = Field(..., min_length=1)
    preferred_language: str = Field(..., min_length=2, max_length=10)
    explanation_level: ExplanationLevel = "plain"


class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1)
    preferred_language: Optional[str] = Field(None, min_length=2, max_length=10)
    explanation_level: Optional[ExplanationLevel] = None


class PatientProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str] = None
    preferred_language: str
    explanation_level: str
