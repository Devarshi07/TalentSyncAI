"""
Auth schemas for signup, login, OAuth, and token responses.
"""
import re
from typing import Optional

from pydantic import BaseModel, field_validator

import config


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username is required")
        v = v.strip().lower()
        if len(v) < config.USERNAME_MIN_LENGTH:
            raise ValueError(f"Username must be at least {config.USERNAME_MIN_LENGTH} characters")
        if len(v) > config.USERNAME_MAX_LENGTH:
            raise ValueError(f"Username must be at most {config.USERNAME_MAX_LENGTH} characters")
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("Username may only contain lowercase letters, numbers, and underscores")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email is required")
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        if len(v) > 255:
            raise ValueError("Email too long")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        if len(v) < config.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username is required")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    auth_provider: str = "local"

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleCallbackRequest(BaseModel):
    """For frontend-initiated OAuth (token exchange flow)."""
    code: str
    redirect_uri: Optional[str] = None
