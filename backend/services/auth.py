"""Supabase Auth service — singleton client + email-gate helper + auth dependency.

Uses the service-role key so the backend can verify JWTs and call
admin APIs (create user, etc.) without user credentials.
"""

from fastapi import Depends, HTTPException, status, Header
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, ALLOWED_EMAIL


_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Return singleton Supabase client (service-role)."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client


def is_allowed_email(email: str) -> bool:
    """Check if email matches the single allowed email (case-insensitive)."""
    return ALLOWED_EMAIL and email.lower() == ALLOWED_EMAIL.lower()


async def verify_token(access_token: str) -> dict:
    """Verify JWT via Supabase and return user payload.

    Raises:
        ValueError: if token invalid/expired
    """
    client = get_supabase()
    response = client.auth.get_user(access_token)
    if response.user is None:
        raise ValueError("Invalid or expired token")
    return response.user


async def sign_in_with_password(email: str, password: str) -> dict:
    """Sign in with email/password. Returns session with access_token."""
    client = get_supabase()
    response = client.auth.sign_in_with_password({"email": email, "password": password})
    if response.session is None:
        raise ValueError("Invalid credentials")
    return response.session


async def sign_up_admin(email: str, password: str) -> dict:
    """Admin-only signup (service-role key bypasses email confirmation).

    Returns the created user object (no session — user must login).
    """
    if not is_allowed_email(email):
        raise ValueError("Email not allowed")
    client = get_supabase()
    response = client.auth.admin.create_user(
        {
            "email": email,
            "password": password,
            "email_confirm": True,
        }
    )
    if response.user is None:
        raise ValueError("Failed to create user")
    return response.user


async def require_auth(authorization: str | None = Header(None)) -> dict:
    """FastAPI dependency: verify Bearer token and return user payload.

    Raises HTTPException 401 if token missing/invalid/expired or email not allowed.
    Attaches user_id to request.state for downstream use.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ")[1]
    try:
        user = await verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Check allowed email
    user_email = getattr(user, "email", None)
    if not user_email or not is_allowed_email(user_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not authorized",
        )

    return user