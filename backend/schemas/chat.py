"""
Chat API request/response schemas.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    thread_id: Optional[str] = None
    context: Optional[dict[str, Any]] = Field(default=None)


class ChatAttachment(BaseModel):
    type: str
    content: Optional[str] = None
    filename: Optional[str] = None


class ChatResponse(BaseModel):
    intent: Literal["resume_tailor", "interview_prep", "general"]
    response: str
    attachments: list[ChatAttachment] = Field(default_factory=list)
    thread_id: Optional[str] = None
