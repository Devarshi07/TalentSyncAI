"""
Auth API: signup, login, refresh, logout, Google OAuth.
"""
import re
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

import config
from core.limiter import limiter
from core.deps import get_current_user_id
from core.logging import get_logger
from db.database import get_db
from db.models import User
from schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    GoogleCallbackRequest,
)
from services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_all_refresh_tokens,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        auth_provider=user.auth_provider or "local",
    )


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    """Create access + refresh tokens for a user."""
    access = create_access_token(user.id)
    refresh = create_refresh_token(db, user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_to_response(user),
    )


def _generate_username_from_email(db: Session, email: str) -> str:
    """Generate a unique username from an email address."""
    base = email.split("@")[0].lower()
    base = re.sub(r"[^a-z0-9_]", "_", base)
    if len(base) < 3:
        base = base + "_user"

    username = base
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}_{counter}"
        counter += 1
    return username


def _find_or_create_google_user(
    db: Session,
    google_id: str,
    email: str,
    name: str,
) -> User:
    """Find existing user by google_id or email, or create a new one."""
    # Check by google_id first
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        return user

    # Check by email — link accounts
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.google_id = google_id
        if user.auth_provider == "local":
            user.auth_provider = "local+google"
        db.commit()
        db.refresh(user)
        logger.info("Linked Google account to existing user", extra={"user_id": user.id, "email": email})
        return user

    # Create new user
    username = _generate_username_from_email(db, email)
    user = User(
        username=username,
        email=email,
        hashed_password=None,
        auth_provider="google",
        google_id=google_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created new Google user", extra={"user_id": user.id, "email": email})
    return user


# ---------- Local Auth ----------


@router.post("/signup", response_model=TokenResponse)
@limiter.limit("5/minute")
def signup(request: Request, body: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user with username, email, and password."""
    try:
        existing = (
            db.query(User)
            .filter((User.username == body.username) | (User.email == body.email))
            .first()
        )
    except SQLAlchemyError as e:
        logger.exception("Database error during signup")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error. Ensure the database is running.",
        ) from e

    if existing:
        if existing.username == body.username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        auth_provider="local",
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during signup (insert)")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error. Please try again.",
        ) from e

    logger.info("User signed up", extra={"user_id": user.id, "username": user.username})
    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with username and password."""
    try:
        user = db.query(User).filter(User.username == body.username).first()
    except SQLAlchemyError as e:
        logger.exception("Database error during login")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error. Ensure the database is running.",
        ) from e

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username not found. Please sign up first.",
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account uses {user.auth_provider} login. Please sign in with {user.auth_provider}.",
        )

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    logger.info("User logged in", extra={"user_id": user.id, "username": user.username})
    return _issue_tokens(db, user)


# ---------- Token Refresh ----------


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for new access + refresh tokens (rotation)."""
    user_id = verify_refresh_token(db, body.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please log in again.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )

    logger.info("Token refreshed", extra={"user_id": user.id})
    return _issue_tokens(db, user)


# ---------- Logout ----------


@router.post("/logout")
def logout(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Revoke all refresh tokens for the current user."""
    count = revoke_all_refresh_tokens(db, user_id)
    logger.info("User logged out", extra={"user_id": user_id, "tokens_revoked": count})
    return {"message": "Logged out successfully", "tokens_revoked": count}


# ---------- Current User ----------


@router.get("/me", response_model=UserResponse)
def me(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Return the current authenticated user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _user_to_response(user)


# ---------- Google OAuth ----------


@router.get("/google")
def google_login():
    """Redirect user to Google's OAuth consent screen."""
    if not config.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
def google_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Handle Google OAuth callback synchronously.
    Exchanges code for tokens, creates/links user, redirects to frontend with tokens.
    """
    if error:
        logger.warning("Google OAuth error", extra={"error": error})
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': error})}"
        )

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    # Exchange code for Google tokens (synchronous httpx)
    try:
        token_resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": config.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
    except Exception as e:
        logger.exception("Failed to exchange Google auth code")
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'token_exchange_failed'})}"
        )

    if token_resp.status_code != 200:
        logger.warning(
            "Google token exchange failed",
            extra={"status": token_resp.status_code, "body": token_resp.text[:500]},
        )
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'token_exchange_failed'})}"
        )

    token_data = token_resp.json()
    google_access_token = token_data.get("access_token")
    if not google_access_token:
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'no_access_token'})}"
        )

    # Fetch user info from Google (synchronous)
    try:
        userinfo_resp = httpx.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
            timeout=10.0,
        )
        if userinfo_resp.status_code != 200:
            return RedirectResponse(
                url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'userinfo_failed'})}"
            )
        google_user = userinfo_resp.json()
    except Exception as e:
        logger.exception("Failed to fetch Google user info")
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'userinfo_failed'})}"
        )

    if not google_user.get("email"):
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'no_email'})}"
        )

    google_id = google_user["sub"]
    email = google_user["email"].lower().strip()
    name = google_user.get("name", "")

    # Find or create user
    try:
        user = _find_or_create_google_user(db, google_id, email, name)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create/link Google user")
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}/auth/callback?{urlencode({'error': 'db_error'})}"
        )

    # Issue our tokens
    access = create_access_token(user.id)
    refresh_tok = create_refresh_token(db, user.id)

    logger.info("Google OAuth login successful", extra={"user_id": user.id, "email": email})

    # Redirect to frontend with tokens
    params = urlencode({
        "access_token": access,
        "refresh_token": refresh_tok,
    })
    return RedirectResponse(url=f"{config.FRONTEND_URL}/auth/callback?{params}")


@router.post("/google/token", response_model=TokenResponse)
def google_token_exchange(
    body: GoogleCallbackRequest,
    db: Session = Depends(get_db),
):
    """
    Alternative flow: frontend sends the Google authorization code directly.
    Useful for SPA / mobile apps that handle the redirect themselves.
    """
    if not config.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    redirect_uri = body.redirect_uri or config.GOOGLE_REDIRECT_URI

    token_resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": body.code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10.0,
    )

    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code with Google.",
        )

    token_data = token_resp.json()
    google_access_token = token_data.get("access_token")
    if not google_access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token from Google")

    userinfo_resp = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"},
        timeout=10.0,
    )
    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not fetch Google user info")

    google_user = userinfo_resp.json()
    if not google_user.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No email from Google")

    google_id = google_user["sub"]
    email = google_user["email"].lower().strip()
    name = google_user.get("name", "")

    user = _find_or_create_google_user(db, google_id, email, name)
    return _issue_tokens(db, user)
