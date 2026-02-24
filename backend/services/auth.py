"""
Auth service: password hashing, JWT access/refresh tokens, and token management.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import config
from db.models import RefreshToken


# --- Password ---

def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Truncates to 72 bytes (bcrypt limit)."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


# --- Access Token ---

def create_access_token(subject: str) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Decode and validate a JWT access token. Returns user_id or None."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None


# --- Refresh Token ---

def _hash_token(token: str) -> str:
    """SHA-256 hash of a refresh token for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(db: Session, user_id: str) -> str:
    """Generate an opaque refresh token, store its hash in DB, return raw token."""
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)

    record = RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(raw_token),
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    return raw_token


def verify_refresh_token(db: Session, raw_token: str) -> str | None:
    """
    Validate a refresh token. Returns user_id if valid, None otherwise.
    Implements rotation: the used token is revoked and caller should issue a new one.
    """
    token_hash = _hash_token(raw_token)
    record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
        .first()
    )
    if not record:
        return None
    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        record.revoked = True
        db.commit()
        return None

    # Rotate: revoke the old token
    record.revoked = True
    db.commit()
    return record.user_id


def revoke_all_refresh_tokens(db: Session, user_id: str) -> int:
    """Revoke all refresh tokens for a user (e.g. on password change or logout-all)."""
    count = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        .update({"revoked": True})
    )
    db.commit()
    return count
