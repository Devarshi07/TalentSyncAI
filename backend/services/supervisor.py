"""
Supervisor Agent: classifies user intent and routes to specialized agents.
Profile editing is handled exclusively via the frontend Profile page.
"""
import json
import re
from typing import Literal

import config
from core.logging import get_logger
from services.gemini_client import generate_with_retry

logger = get_logger(__name__)

Intent = Literal["resume_tailor", "interview_prep", "general"]
VALID_INTENTS = {"resume_tailor", "interview_prep", "general"}

SUPERVISOR_SYSTEM_PROMPT = """You are the supervisor agent for a Job Assistant AI platform.
Your ONLY job is to classify the user's message into exactly one intent.

INTENTS:
- resume_tailor: User wants to create, tailor, customize, or generate a resume/CV for a job.
  Triggers: "tailor my resume", "generate resume", "create CV", "resume for [role]", job descriptions pasted, "make my resume for".
- interview_prep: User wants interview help — practice questions, behavioral prep, technical prep, company-specific prep.
  Triggers: "interview prep", "interview questions", "prepare for interview", "what will they ask", "help me prep for".
- general: Greetings, career advice, profile editing requests, unclear requests, or anything else.
  Note: If user asks to edit/update their profile, classify as general (profile editing is done via the UI, not chat).

RULES:
- If the message contains a full job description (multi-line with requirements/responsibilities), classify as resume_tailor.
- If the message mentions both resume AND interview, pick the PRIMARY ask.
- Profile edit requests → general (the chat will redirect them to the Profile page).
- When in doubt, classify as general.

Respond with ONLY: {"intent": "<intent>"}
No other text."""


def classify_intent(message: str) -> Intent:
    if not message or not message.strip():
        return "general"

    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set; falling back to general")
        return "general"

    try:
        content = generate_with_retry(
            contents=message.strip()[:2000],
            system_instruction=SUPERVISOR_SYSTEM_PROMPT,
            temperature=0,
        )
        return _parse_intent(content)
    except Exception as e:
        logger.exception("Supervisor classification failed", extra={"error": str(e)})
        return "general"


def _parse_intent(content: str) -> Intent:
    content = (content or "").strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)
    json_match = re.search(r"\{[^{}]*\"intent\"[^{}]*\}", content)
    if json_match:
        content = json_match.group(0)
    try:
        data = json.loads(content)
        intent = (data.get("intent") or "").strip().lower()
        if intent in VALID_INTENTS:
            return intent
        # Map old profile_edit intent to general
        if intent == "profile_edit":
            return "general"
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Failed to parse supervisor response", extra={"content": content[:200]})
    return "general"
