"""
Authentication API router.

Provides endpoints for user registration, login, token refresh,
current user retrieval, and logout with httpOnly cookie support
for refresh tokens.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import (
    AuthService,
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    UserNotFoundError,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Cookie configuration
# ---------------------------------------------------------------------------

REFRESH_COOKIE_NAME = "researchmind_refresh_token"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Set the refresh token as an httpOnly, secure cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        # Secure=True in production; allow HTTP for local dev
        secure=False,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth",
        httponly=True,
        samesite="lax",
        secure=False,
    )


def _get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(db)


# ---------------------------------------------------------------------------
# Helper: extract current user from Authorization header or cookie
# ---------------------------------------------------------------------------

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    FastAPI dependency that extracts and validates the current user.

    Checks the Authorization header first, then falls back to the
    refresh cookie for read-only identity (avoids extra DB calls).
    """
    auth_service = _get_auth_service(db)
    token = _extract_access_token(request)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(token)
    if token_data is None or token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = auth_service.get_user_by_id(UUID(token_data.sub))
        return auth_service.build_user_response(user)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


def _extract_access_token(request: Request) -> str | None:
    """Extract Bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    response: Response,
    service: AuthService = Depends(_get_auth_service),
) -> dict:
    """
    Register a new user account.

    Returns an access token and sets a refresh token as an httpOnly
    cookie. The access token must be sent as ``Authorization: Bearer
    <token>`` on subsequent requests.
    """
    try:
        user, access_token, refresh_token = service.register_user(user_data)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except DuplicateUsernameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": service.build_user_response(user),
    }


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    response: Response,
    service: AuthService = Depends(_get_auth_service),
) -> dict:
    """
    Authenticate with email and password.

    Returns an access token and sets a refresh token as an httpOnly
    cookie.
    """
    try:
        user, access_token, refresh_token = service.authenticate_user(
            credentials.email, credentials.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": service.build_user_response(user),
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """
    Refresh the access token using the refresh token cookie.

    Reads the httpOnly ``researchmind_refresh_token`` cookie, validates
    it, and returns a new access token + a new refresh token (rotated).
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found. Please log in again.",
        )

    service = _get_auth_service(db)
    result = service.refresh_user_session(refresh_token)

    if result is None:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please log in again.",
        )

    user, new_access, new_refresh = result
    _set_refresh_cookie(response, new_refresh)

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "user": service.build_user_response(user),
    }


@router.get("/me", response_model=UserResponse)
def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Return the currently authenticated user's profile.

    Requires a valid access token in the ``Authorization`` header.
    """
    return current_user


@router.post("/logout")
def logout(response: Response) -> dict:
    """
    Log out by clearing the refresh token cookie.

    The frontend should also discard the in-memory access token.
    """
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}
