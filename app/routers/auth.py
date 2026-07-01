from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from supabase_auth.errors import AuthApiError
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.database import get_supabase
from app.middleware.auth import bearer_scheme, get_current_user
import logging

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    auth_client = get_supabase_auth()
    admin = get_supabase()
    try:
        response = auth_client.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Please check your email and try again.",
            )
        # Create user_profiles row
        #maybe auth.users or user_profiles or user_settings
        supabase.table("user_profiles").insert({
            "user_id": response.user.id,
        }).execute()

        #! added this for sessions that are not granted immediately(email confirmation is pending).

        token = response.session.access_token if response.session else None

        return AuthResponse(
            access_token=token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except HTTPException:
        raise
    except AuthApiError as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Supabase signup rate limit exceeded.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. This email may already be registered.",
        )
    except Exception as e:
        logger.exception(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again.",
        )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    auth_client = get_supabase_auth()
    try:
        response = auth_client.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Email not confirmed. Check your inbox or disable email "
                    "confirmation in Supabase Auth settings, then log in."
                ),
            )

        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except HTTPException:
        raise
    except AuthApiError as e:
        logger.warning("Login rejected by Supabase: %s", e)
        status_code, detail = map_auth_error(e, context="login")
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        logger.exception(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Revoke refresh tokens for the authenticated user (global scope).
    Access JWTs remain valid until expiry; the client must discard the token.
    """
    supabase = get_supabase()
    try:
        supabase.auth.admin.sign_out(credentials.credentials, scope="global")
    except Exception as e:
        logger.warning("Supabase admin sign_out failed for user %s: %s", user["id"], e)
    return
