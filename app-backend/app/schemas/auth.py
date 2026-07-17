from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.utils.validation import NonEmptyStr, OptionalNonEmptyStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: NonEmptyStr = Field(..., min_length=8)
    full_name: OptionalNonEmptyStr = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: NonEmptyStr = Field(..., min_length=1)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserProfile(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str] = None
    preferred_language: str = "en"
    explanation_level: str = "plain"  # plain | detailed
