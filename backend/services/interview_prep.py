"""
Interview Prep Agent
====================
Takes user profile + job description/company → generates targeted interview prep.

Strategy:
1. Extract company name and role from user message / context
2. Search the web for common interview questions at that company (if possible)
3. Combine profile strengths with JD requirements
4. Generate: behavioral questions, technical questions, and suggested talking points
"""
import json

import httpx

import config
from core.logging import get_logger
from services.gemini_client import generate_with_retry
from schemas.profile import ProfileSchema

logger = get_logger(__name__)

INTERVIEW_SYSTEM_PROMPT = """You are an expert career coach and interview preparation specialist.

Given a candidate's profile and a target job (role + company + job description), generate comprehensive interview preparation.

STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS:

## Company Overview
Brief 2-3 sentence overview of the company and what they look for in candidates.

## Behavioral Questions (5-6 questions)
For each question:
- The question
- Why they ask it (what they're evaluating)
- A suggested STAR-format answer outline using the candidate's actual experience

## Technical Questions (5-6 questions)
Role-specific technical questions they're likely to ask, based on the job requirements.
For each: the question + key points to cover.

## Questions to Ask the Interviewer (3-4)
Smart questions the candidate should ask, tailored to the role.

## Key Talking Points
3-4 specific experiences/projects from the candidate's profile that best demonstrate fitness for this role.

RULES:
- Use the candidate's ACTUAL experience and projects in your suggested answers — be specific, reference their real work.
- If you know common interview patterns for this company, incorporate them.
- Tailor technical questions to the specific tech stack mentioned in the JD.
- Be practical and actionable, not generic."""


def _search_company_info(company: str, role: str) -> str:
    """Try to fetch relevant interview info from the web."""
    query = f"{company} {role} interview questions"
    try:
        resp = httpx.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": config.GEMINI_API_KEY,  # reuse key if it works
                "cx": "search-engine-id",
                "q": query,
                "num": 3,
            },
            timeout=5.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            snippets = [item.get("snippet", "") for item in data.get("items", [])]
            return "\n".join(snippets)
    except Exception:
        pass
    return ""


def _extract_company_and_role(message: str) -> tuple[str, str]:
    """Try to extract company name and role from the user's message."""
    if not config.GEMINI_API_KEY:
        return ("", "")

    try:
        content = generate_with_retry(
            contents=f"Extract the company name and job role from this message. Respond with JSON only: {{\"company\": \"...\", \"role\": \"...\"}}\n\nMessage: {message[:500]}",
            temperature=0,
        )
        content = content.strip()
        if "```" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]
        data = json.loads(content)
        return (data.get("company", ""), data.get("role", ""))
    except Exception:
        return ("", "")


def generate_interview_prep(profile: ProfileSchema, message: str, context: dict | None = None) -> str:
    """
    Generate interview preparation content based on profile and target role.
    """
    if not config.GEMINI_API_KEY:
        return "Interview prep requires the Gemini API key to be configured."

    # Extract job description from context or message
    job_desc = ""
    if context and isinstance(context.get("job_description"), str):
        job_desc = context["job_description"].strip()

    # Extract company and role
    company, role = _extract_company_and_role(message)

    # Build profile summary for the LLM
    profile_dict = profile.model_dump()
    profile_summary = json.dumps({
        "name": profile_dict.get("personal", {}).get("name", ""),
        "experience": profile_dict.get("experience", []),
        "projects": profile_dict.get("projects", []),
        "skills": profile_dict.get("skills", {}),
        "education": profile_dict.get("education", []),
        "leadership": profile_dict.get("leadership", []),
    }, indent=2)

    # Build the prompt
    prompt_parts = [f"CANDIDATE PROFILE:\n{profile_summary}"]

    if job_desc:
        prompt_parts.append(f"\nJOB DESCRIPTION:\n{job_desc}")
    if company:
        prompt_parts.append(f"\nTARGET COMPANY: {company}")
    if role:
        prompt_parts.append(f"\nTARGET ROLE: {role}")

    prompt_parts.append(f"\nUSER REQUEST: {message}")
    prompt_parts.append("\nGenerate comprehensive interview preparation for this candidate and role.")

    prompt = "\n".join(prompt_parts)

    try:
        content = generate_with_retry(
            contents=prompt,
            system_instruction=INTERVIEW_SYSTEM_PROMPT,
            temperature=0.4,
        )
        return content or "I couldn't generate interview prep right now. Please try again."
    except Exception as e:
        logger.exception("Interview prep generation failed", extra={"error": str(e)})
        return "Sorry, I couldn't generate interview prep right now. Please try again."
