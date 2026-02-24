"""
General Agent
=============
Handles general career advice, greetings, catch-all, and profile edit redirects.
"""
import json
import re

import config
from core.logging import get_logger
from services.gemini_client import generate_with_retry
from schemas.profile import ProfileSchema

logger = get_logger(__name__)

# Keywords that indicate the user wants to edit their profile
PROFILE_EDIT_KEYWORDS = [
    "edit profile", "update profile", "change my", "add experience", "add project",
    "update my", "edit my", "modify profile", "change profile",
]

GENERAL_SYSTEM_PROMPT = """You are a friendly AI career assistant called "Job Assistant".

You help with:
- Career advice and strategy
- Resume tips and best practices
- Job search guidance
- Skill development recommendations

If the user's profile is provided, personalize your advice.

Keep responses concise (2-4 paragraphs max) and actionable.
Mention that they can ask you to "tailor my resume for [role]" or "prep me for an interview at [company]" for those features.

IMPORTANT: If the user asks to edit/update their profile, tell them to use the Profile page in the sidebar. Profile editing is done through the UI, not through chat."""


def generate_response(profile: ProfileSchema, message: str) -> str:
    msg_lower = message.lower().strip()

    # Check for profile edit intent — redirect to UI
    if any(kw in msg_lower for kw in PROFILE_EDIT_KEYWORDS):
        return (
            "Profile editing is done through the **Profile** page — click \"Profile\" "
            "in the sidebar to update your information. You can add or edit your:\n\n"
            "• Personal info (name, email, phone, links)\n"
            "• Education\n"
            "• Work experience (with bullet points)\n"
            "• Projects (with tech stack and bullets)\n"
            "• Technical skills\n"
            "• Leadership & achievements\n\n"
            "Once your profile is complete, I can tailor resumes and generate "
            "interview prep for you!"
        )

    if not config.GEMINI_API_KEY:
        return (
            "I'm your Job Assistant! I can help with:\n\n"
            "• **Resume tailoring** — \"Tailor my resume for [role] at [company]\"\n"
            "• **Interview prep** — \"Help me prep for an interview at [company]\"\n"
            "• **Career advice** — Ask me anything!\n\n"
            "Complete your **Profile** in the sidebar for personalized help."
        )

    profile_dict = profile.model_dump()
    has_profile = bool(profile_dict.get("personal", {}).get("name"))

    prompt = message.strip()
    if has_profile:
        summary = json.dumps({
            "name": profile_dict["personal"].get("name", ""),
            "target_roles": profile_dict.get("preferences", {}).get("target_roles", []),
            "skills": list(profile_dict.get("skills", {}).get("technical", []))[:10],
        })
        prompt = f"[User profile: {summary}]\n\n{prompt}"

    try:
        content = generate_with_retry(
            contents=prompt,
            system_instruction=GENERAL_SYSTEM_PROMPT,
            temperature=0.5,
        )
        return content or "I'm here to help! Try asking me to tailor your resume or prep for an interview."
    except Exception as e:
        logger.exception("General agent failed", extra={"error": str(e)})
        return "I'm here to help! You can ask me to tailor your resume, prepare for interviews, or give career advice."
