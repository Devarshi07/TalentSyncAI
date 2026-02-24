"""
Production-grade configuration with validation.
All settings are loaded from environment variables.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend/ and project root (for start_app.sh)
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from typing import List


def _get_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).lower()
    return val in ("1", "true", "yes")


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


# API
API_PREFIX = os.getenv("API_PREFIX", "/api")
API_TITLE = os.getenv("API_TITLE", "Job Assistant API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
DEBUG = _get_bool("DEBUG", False)

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = _get_int("PORT", 5001)

# Database - PostgreSQL by default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/job_assistant",
)
DB_POOL_SIZE = _get_int("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = _get_int("DB_MAX_OVERFLOW", 10)

# Gemini (Google) for all LLM features
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# CORS - must be explicit in production (comma-separated origins)
_DEFAULT_CORS = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5001,http://127.0.0.1:5001"
CORS_ORIGINS: List[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", _DEFAULT_CORS).split(",")
    if o.strip()
]
# Allow credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = _get_bool("CORS_ALLOW_CREDENTIALS", True)

# Rate limiting
RATE_LIMIT_ENABLED = _get_bool("RATE_LIMIT_ENABLED", True)
RATE_LIMIT_PER_MINUTE = _get_int("RATE_LIMIT_PER_MINUTE", 60)

# Profile limits (prevent abuse)
PROFILE_MAX_SIZE_BYTES = _get_int("PROFILE_MAX_SIZE_BYTES", 100_000)  # ~100KB
PROFILE_MAX_EDUCATION_ITEMS = _get_int("PROFILE_MAX_EDUCATION_ITEMS", 10)
PROFILE_MAX_EXPERIENCE_ITEMS = _get_int("PROFILE_MAX_EXPERIENCE_ITEMS", 20)
PROFILE_MAX_PROJECT_ITEMS = _get_int("PROFILE_MAX_PROJECT_ITEMS", 15)
PROFILE_MAX_BULLETS_PER_EXP = _get_int("PROFILE_MAX_BULLETS_PER_EXP", 10)
PROFILE_MAX_SKILLS = _get_int("PROFILE_MAX_SKILLS", 50)

# User ID validation
USER_ID_MAX_LENGTH = _get_int("USER_ID_MAX_LENGTH", 255)
USER_ID_ALLOWED_PATTERN = r"^[a-zA-Z0-9._@+-]+$"

# JWT Auth
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)  # 7 days

# Password policy
PASSWORD_MIN_LENGTH = _get_int("PASSWORD_MIN_LENGTH", 8)
USERNAME_MIN_LENGTH = _get_int("USERNAME_MIN_LENGTH", 3)
USERNAME_MAX_LENGTH = _get_int("USERNAME_MAX_LENGTH", 50)

# Refresh tokens
REFRESH_TOKEN_EXPIRE_DAYS = _get_int("REFRESH_TOKEN_EXPIRE_DAYS", 30)

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5001/api/auth/google/callback")

# Frontend URL (for OAuth redirect after callback)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
