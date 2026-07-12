"""Auth endpoints — login + admin-only signup.

See BLUEPRINT.md §10 for API contract.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from schemas import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from services.auth import get_supabase, is_allowed_email, sign_in_with_password, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(authorization: str | None = None):
    """Dependency: verify Bearer token and return user payload."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ")[1]
    try:
        user = await verify_token(token)
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """Sign in with email + password. Returns access token on success."""
    if not is_allowed_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not authorized",
        )

    client = get_supabase()
    response = client.auth.sign_in_with_password({
        "email": payload.email,
        "password": payload.password,
    })

    if response.session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return LoginResponse(
        access_token=response.session.access_token,
        token_type="bearer",
        expires_in=response.session.expires_in,
    )


@router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupRequest, current_user=Depends(get_current_user)):
    """Admin-only signup — creates a new user in Supabase Auth.

    Only the ALLOWED_EMAIL user can call this (enforced by get_current_user
    + is_allowed_email check on the caller's email).
    """
    caller_email = getattr(current_user, "email", None)
    if not caller_email or not is_allowed_email(caller_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the allowed admin email can create users",
        )

    if not is_allowed_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create users with the allowed email",
        )

    client = get_supabase()
    response = client.auth.admin.create_user({
        "email": payload.email,
        "password": payload.password,
        "email_confirm": True,
    })

    if response.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user",
        )

    return SignupResponse(
        user_id=response.user.id,
        email=response.user.email,
    )