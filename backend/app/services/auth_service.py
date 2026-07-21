"""
Authentication service for the ResearchMind AI platform.

Handles user registration, login, JWT token management, and
password hashing using passlib with bcrypt.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.auth import TokenData, UserCreate, UserResponse


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(user_id: UUID) -> str:
    """Create a short-lived JWT access token for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """Create a long-lived JWT refresh token for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenData | None:
    """
    Decode and validate a JWT token.

    Returns ``TokenData`` if the token is valid, ``None`` otherwise.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        sub: str | None = payload.get("sub")
        exp: int | None = payload.get("exp")
        token_type: str | None = payload.get("type")

        if sub is None or exp is None or token_type is None:
            return None

        return TokenData(sub=sub, exp=exp, type=token_type)
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class AuthError(Exception):
    """Base exception for authentication errors."""


class UserNotFoundError(AuthError):
    """Raised when a user is not found."""


class DuplicateEmailError(AuthError):
    """Raised when an email is already registered."""


class DuplicateUsernameError(AuthError):
    """Raised when a username is already taken."""


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class UserRepository(BaseRepository[User]):
    """Repository for User-specific database queries."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email."""
        from sqlalchemy import select

        stmt = select(User).where(User.email == email)
        return self._session.scalar(stmt)

    def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by username."""
        from sqlalchemy import select

        stmt = select(User).where(User.username == username)
        return self._session.scalar(stmt)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AuthService:
    """Service for authentication operations.

    Parameters
    ----------
    session : Session
        The SQLAlchemy ORM session to use.
    """

    def __init__(self, session: Session) -> None:
        self._repository = UserRepository(session)
        self._session = session

    def register_user(self, user_data: UserCreate) -> tuple[User, str, str]:
        """
        Register a new user.

        Returns
        -------
        tuple[User, str, str]
            The created user, access token, and refresh token.

        Raises
        ------
        DuplicateEmailError
            If the email is already taken.
        DuplicateUsernameError
            If the username is already taken.
        """
        # Check uniqueness
        if self._repository.get_by_email(user_data.email) is not None:
            raise DuplicateEmailError(
                f"Email '{user_data.email}' is already registered."
            )
        if self._repository.get_by_username(user_data.username) is not None:
            raise DuplicateUsernameError(
                f"Username '{user_data.username}' is already taken."
            )

        user = self._repository.create(
            email=user_data.email,
            username=user_data.username,
            password_hash=hash_password(user_data.password),
        )
        self._session.commit()
        self._session.refresh(user)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return user, access_token, refresh_token

    def authenticate_user(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Authenticate a user by email and password.

        Returns
        -------
        tuple[User, str, str]
            The authenticated user, access token, and refresh token.

        Raises
        ------
        InvalidCredentialsError
            If the email or password is incorrect.
        """
        user = self._repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return user, access_token, refresh_token

    def refresh_user_session(self, refresh_token: str) -> tuple[User, str, str] | None:
        """
        Validate a refresh token and issue new tokens.

        Returns
        -------
        tuple[User, str, str] or None
            The user, new access token, and new refresh token, or None if
            the refresh token is invalid/expired.
        """
        token_data = decode_token(refresh_token)
        if token_data is None or token_data.type != "refresh":
            return None

        user_id = UUID(token_data.sub)
        user = self._repository.get_by_id(user_id)
        if user is None:
            return None

        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)
        return user, new_access, new_refresh

    def get_user_by_id(self, user_id: UUID) -> User:
        """Retrieve a user by their ID."""
        user = self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with id '{user_id}' not found.")
        return user

    @staticmethod
    def build_user_response(user: User) -> UserResponse:
        """Build a UserResponse from a User ORM instance."""
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            created_at=user.created_at,
        )
