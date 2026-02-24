"""
Chat API: Multi-agent orchestration with thread-based history.

Flow:
  User message (with thread_id) → Save user msg → Supervisor → Agent → Save assistant msg
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.deps import get_current_user_id
from core.limiter import limiter
from core.logging import get_logger
from db.database import get_db
from db.models import Profile, ChatThread, ChatMessage
from schemas.chat import ChatRequest, ChatResponse, ChatAttachment
from schemas.profile import ProfileSchema
from services.supervisor import classify_intent
from services.resume_tailor import generate_tailored_resume
from services.interview_prep import generate_interview_prep
from services.general_agent import generate_response as general_response

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

USER_STORAGE_LIMIT = 3 * 1024 * 1024  # 3MB


def _load_profile(db: Session, user_id: str) -> ProfileSchema:
    row = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not row or not row.data:
        return ProfileSchema()
    try:
        return ProfileSchema(**json.loads(row.data))
    except (json.JSONDecodeError, TypeError):
        return ProfileSchema()


def _is_profile_complete(profile: ProfileSchema) -> bool:
    return bool(profile.personal.name and (profile.experience or profile.projects))


def _get_user_storage(db: Session, user_id: str) -> int:
    result = db.execute(
        text("""
            SELECT COALESCE(SUM(
                LENGTH(m.content) + COALESCE(LENGTH(CAST(m.attachments AS TEXT)), 0)
            ), 0)
            FROM chat_messages m
            JOIN chat_threads t ON m.thread_id = t.id
            WHERE t.user_id = :uid
        """),
        {"uid": user_id},
    )
    return int(result.scalar() or 0)


def _auto_delete_oldest_thread(db: Session, user_id: str):
    """Delete the oldest thread to free up space."""
    oldest = (
        db.query(ChatThread)
        .filter(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.asc())
        .first()
    )
    if oldest:
        logger.info("Auto-deleting oldest thread for storage", extra={"user_id": user_id, "thread_id": oldest.id})
        db.delete(oldest)
        db.commit()


def _generate_title(message: str) -> str:
    clean = message.strip().replace("\n", " ")
    return clean[:47] + "..." if len(clean) > 50 else clean


def _save_message(db: Session, thread_id: str, role: str, content: str,
                  intent: str = None, attachments: list = None):
    """Save a message to the thread."""
    att_json = None
    if attachments:
        att_json = [a.model_dump() if hasattr(a, 'model_dump') else a for a in attachments]

    msg = ChatMessage(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        role=role,
        content=content,
        intent=intent,
        attachments=att_json,
    )
    db.add(msg)


# ---- Agent handlers ----

def _handle_resume_tailor(profile, message, context):
    if not _is_profile_complete(profile):
        return (
            "I need your profile to tailor a resume. Head to the **Profile** page in the "
            "sidebar and fill in your name, experience, and projects first!",
            [],
        )
    job_desc = ""
    if context and isinstance(context.get("job_description"), str):
        job_desc = context["job_description"].strip()
    if not job_desc:
        job_desc = message.strip()
    try:
        latex = generate_tailored_resume(profile, job_desc)
        return (
            "Here's your tailored resume! Download the LaTeX file and compile it on "
            "[Overleaf](https://overleaf.com) or any LaTeX editor.\n\n"
            "I've rewritten your experience and project bullets to emphasize the most "
            "relevant skills for this role. Your template formatting is preserved exactly.",
            [ChatAttachment(type="latex", content=latex, filename="tailored_resume.tex")],
        )
    except Exception as e:
        logger.exception("Resume tailor failed", extra={"error": str(e)})
        return ("Sorry, I couldn't generate your resume right now. Please try again.", [])


def _handle_interview_prep(profile, message, context):
    if not _is_profile_complete(profile):
        return (
            "I need your profile for personalized interview prep. Please complete your "
            "**Profile** page first (experience, projects, skills)!",
            [],
        )
    try:
        response = generate_interview_prep(profile, message, context)
        return (response, [])
    except Exception as e:
        logger.exception("Interview prep failed", extra={"error": str(e)})
        return ("Sorry, I couldn't generate interview prep right now. Please try again.", [])


def _handle_general(profile, message):
    try:
        response = general_response(profile, message)
        return (response, [])
    except Exception as e:
        logger.exception("General agent failed", extra={"error": str(e)})
        return (
            "I'm your Job Assistant! Try:\n\n"
            "• \"Tailor my resume for [role] at [company]\"\n"
            "• \"Help me prep for an interview at [company]\"\n"
            "• Or ask me anything about your career!",
            [],
        )


# ---- Main endpoint ----

@router.post("", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat(
    request: Request,
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    thread_id = body.thread_id

    # Auto-create thread if not provided
    if not thread_id:
        thread = ChatThread(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=_generate_title(body.message),
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        thread_id = thread.id
    else:
        # Verify thread belongs to user
        thread = (
            db.query(ChatThread)
            .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
            .first()
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Update title if it's still "New chat" (first real message)
        if thread.title == "New chat":
            thread.title = _generate_title(body.message)

    # Check storage limit
    storage = _get_user_storage(db, user_id)
    if storage > USER_STORAGE_LIMIT:
        _auto_delete_oldest_thread(db, user_id)

    # Save user message
    _save_message(db, thread_id, "user", body.message)

    # Classify intent and route
    intent = classify_intent(body.message)
    profile = _load_profile(db, user_id)
    logger.info("Intent classified", extra={"user_id": user_id, "intent": intent, "thread_id": thread_id})

    if intent == "resume_tailor":
        response_text, attachments = _handle_resume_tailor(profile, body.message, body.context)
    elif intent == "interview_prep":
        response_text, attachments = _handle_interview_prep(profile, body.message, body.context)
    else:
        response_text, attachments = _handle_general(profile, body.message)

    # Save assistant message
    _save_message(db, thread_id, "assistant", response_text, intent=intent, attachments=attachments)

    # Update thread timestamp
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    if thread:
        from sqlalchemy.sql import func
        thread.updated_at = func.now()

    db.commit()

    return ChatResponse(
        intent=intent,
        response=response_text,
        attachments=attachments,
        thread_id=thread_id,
    )
