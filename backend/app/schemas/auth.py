"""
Pydantic schemas for authentication.

Defines request/response models for register, login, and token
endpoints following Pydantic v2 conventions.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Schema for registering a new user."""

    email: str = Field(
        ...,
        max_length=320,
        description="Email address",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Username",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
    )


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str = Field(
        ...,
        description="Email address",
    )
    password: str = Field(
        ...,
        description="Password",
    )


class UserResponse(BaseModel):
    """Schema for returning user data in API responses."""

    id: UUID
    email: str
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token responses (login, refresh)."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for decoded token payload."""

    sub: str  # user_id as string
    exp: int
    type: str = "access"  # "access" or "refresh"
