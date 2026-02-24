"""
Profile API with resume PDF import support.
Requires authentication via Bearer token.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

import config
from core.deps import get_current_user_id
from db.database import get_db
from db.models import Profile
from schemas.profile import ProfileSchema
from core.logging import get_logger

router = APIRouter(prefix="/profile", tags=["profile"])
logger = get_logger(__name__)


def _profile_to_schema(data: str | None) -> ProfileSchema:
    if not data:
        return ProfileSchema()
    try:
        return ProfileSchema(**json.loads(data))
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse profile data", extra={"error": str(e)})
        return ProfileSchema()


@router.get("", response_model=ProfileSchema)
def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user profile."""
    row = db.query(Profile).filter(Profile.user_id == user_id).first()
    return _profile_to_schema(row.data if row else None)


@router.put("", response_model=ProfileSchema)
def update_profile(
    profile: ProfileSchema,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create or update user profile."""
    data_str = profile.model_dump_json()
    if len(data_str.encode("utf-8")) > config.PROFILE_MAX_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Profile size exceeds limit")

    row = db.query(Profile).filter(Profile.user_id == user_id).first()
    try:
        if row:
            row.data = data_str
        else:
            row = Profile(user_id=user_id, data=data_str)
            db.add(row)
        db.commit()
        db.refresh(row)
        return _profile_to_schema(row.data)
    except Exception:
        db.rollback()
        logger.exception("Failed to save profile", extra={"user_id": user_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save profile")


@router.post("/import-resume")
async def import_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF resume → parse it → save as profile.
    Returns the parsed profile data.
    """
    # Validate file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    # Read file
    try:
        pdf_bytes = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the uploaded file.")

    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    # Parse
    from services.resume_parser import parse_resume_to_profile

    try:
        profile_data = parse_resume_to_profile(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Resume import failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to parse resume. Please try again.")

    # Validate through schema
    try:
        profile = ProfileSchema(**profile_data)
    except Exception:
        profile = ProfileSchema()
        logger.warning("Parsed data failed schema validation, returning partial")

    # Save to DB
    data_str = profile.model_dump_json()
    row = db.query(Profile).filter(Profile.user_id == user_id).first()
    try:
        if row:
            row.data = data_str
        else:
            row = Profile(user_id=user_id, data=data_str)
            db.add(row)
        db.commit()
        logger.info("Resume imported to profile", extra={"user_id": user_id})
    except Exception:
        db.rollback()
        logger.exception("Failed to save imported profile")

    return {
        "message": "Resume imported successfully! Review your profile to make any adjustments.",
        "profile": profile.model_dump(),
    }
