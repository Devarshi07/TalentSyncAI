"""
Threads API: manage chat threads and message history.
Enforces per-user storage limit.
"""
import uuid
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func, text
from pydantic import BaseModel, Field

from core.deps import get_current_user_id
from core.logging import get_logger
from db.database import get_db
from db.models import ChatThread, ChatMessage

router = APIRouter(prefix="/threads", tags=["threads"])
logger = get_logger(__name__)

# 3MB per user storage limit
USER_STORAGE_LIMIT_BYTES = 3 * 1024 * 1024


# ---- Schemas ----

class ThreadCreate(BaseModel):
    title: str = "New chat"

class ThreadResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ThreadListResponse(BaseModel):
    threads: list[ThreadResponse]
    storage_used: int  # bytes
    storage_limit: int

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    intent: Optional[str] = None
    attachments: Optional[list] = None
    created_at: str

    class Config:
        from_attributes = True

class ThreadDetailResponse(BaseModel):
    thread: ThreadResponse
    messages: list[MessageResponse]


# ---- Helpers ----

def _get_user_storage(db: Session, user_id: str) -> int:
    """Calculate total storage used by a user's chat messages in bytes."""
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


def _generate_title(message: str) -> str:
    """Generate a short title from the first message."""
    clean = message.strip().replace("\n", " ")
    if len(clean) <= 50:
        return clean
    return clean[:47] + "..."


# ---- Endpoints ----

@router.get("", response_model=ThreadListResponse)
def list_threads(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=100),
):
    """List user's chat threads, most recent first."""
    threads = (
        db.query(ChatThread)
        .filter(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.desc())
        .limit(limit)
        .all()
    )
    storage = _get_user_storage(db, user_id)

    return ThreadListResponse(
        threads=[
            ThreadResponse(
                id=t.id, title=t.title,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
            )
            for t in threads
        ],
        storage_used=storage,
        storage_limit=USER_STORAGE_LIMIT_BYTES,
    )


@router.post("", response_model=ThreadResponse, status_code=201)
def create_thread(
    body: ThreadCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new chat thread."""
    thread = ChatThread(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=body.title,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    logger.info("Thread created", extra={"user_id": user_id, "thread_id": thread.id})

    return ThreadResponse(
        id=thread.id, title=thread.title,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
def get_thread(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a thread with all its messages."""
    thread = (
        db.query(ChatThread)
        .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return ThreadDetailResponse(
        thread=ThreadResponse(
            id=thread.id, title=thread.title,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
        ),
        messages=[
            MessageResponse(
                id=m.id, role=m.role, content=m.content,
                intent=m.intent, attachments=m.attachments,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.delete("/{thread_id}")
def delete_thread(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a thread and all its messages."""
    thread = (
        db.query(ChatThread)
        .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    db.delete(thread)  # CASCADE deletes messages
    db.commit()
    logger.info("Thread deleted", extra={"user_id": user_id, "thread_id": thread_id})
    return {"message": "Thread deleted"}


@router.patch("/{thread_id}")
def update_thread_title(
    thread_id: str,
    body: ThreadCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update thread title."""
    thread = (
        db.query(ChatThread)
        .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.title = body.title
    db.commit()
    return {"message": "Title updated"}
