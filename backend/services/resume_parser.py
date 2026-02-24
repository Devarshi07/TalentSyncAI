"""
Resume Parser Agent
===================
Extracts text from a PDF resume and uses Gemini to parse it into
structured profile fields matching the ProfileSchema.
"""
import json
import io

import config
from core.logging import get_logger
from services.gemini_client import generate_with_retry

logger = get_logger(__name__)

PARSER_SYSTEM_PROMPT = """You are an expert resume parser. Given raw text extracted from a PDF resume, extract structured data.

Return ONLY valid JSON matching this exact structure:
{
  "personal": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": ""
  },
  "education": [
    {
      "institution": "",
      "location": "",
      "degree": "",
      "start_date": "",
      "end_date": "",
      "is_current": false,
      "details": ""
    }
  ],
  "experience": [
    {
      "role": "",
      "company": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "is_current": false,
      "description": "Combine ALL bullet points for this role into a single paragraph description."
    }
  ],
  "projects": [
    {
      "name": "",
      "tech_stack": ["tech1", "tech2"],
      "url": "",
      "description": "Combine all bullet points into a single paragraph description."
    }
  ],
  "skills_categories": [
    {"category": "Languages/Database", "items": ["Python", "C++", "MySQL"]},
    {"category": "Libraries/Frameworks", "items": ["React.js", "FastAPI"]},
    {"category": "DevOps/Cloud", "items": ["AWS", "Docker"]}
  ],
  "leadership": [
    {"description": "Full achievement description as a single line"}
  ],
  "preferences": {
    "target_roles": [],
    "industries": []
  }
}

RULES:
- For dates, use format like "Sep 2024", "Jan 2026", etc.
- If a role says "Present" or is clearly current, set is_current to true and leave end_date empty.
- For experience and projects, combine ALL bullet points into a single flowing description paragraph (not individual bullets).
- For skills, group them into categories as shown in the resume (Languages, Frameworks, DevOps, ML, etc).
- For leadership/achievements, each item is a single description string.
- Extract LinkedIn and GitHub URLs if present.
- Return ONLY the JSON, no markdown fences, no explanation."""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using basic methods."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except ImportError:
        logger.warning("PyMuPDF not installed, trying pdfplumber")

    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text.strip()
    except ImportError:
        logger.error("No PDF library available. Install PyMuPDF: pip install PyMuPDF")
        raise ValueError("PDF parsing requires PyMuPDF. Install with: pip install PyMuPDF")


def parse_resume_to_profile(pdf_bytes: bytes) -> dict:
    """
    Parse a PDF resume into structured profile data.
    Returns a dict matching ProfileSchema structure.
    """
    # 1. Extract text
    text = extract_text_from_pdf(pdf_bytes)
    if not text:
        raise ValueError("Could not extract text from the PDF. The file may be image-based or empty.")

    logger.info("Extracted resume text", extra={"char_count": len(text)})

    # 2. Use Gemini to parse into structured data
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required for resume parsing.")

    content = generate_with_retry(
        contents=f"Parse this resume text into structured JSON:\n\n{text[:8000]}",
        system_instruction=PARSER_SYSTEM_PROMPT,
        temperature=0,
    )

    # Strip markdown fences if present
    if "```" in content:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]

    try:
        profile_data = json.loads(content)
        logger.info("Resume parsed successfully", extra={"sections": list(profile_data.keys())})
        return profile_data
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini response as JSON", extra={"error": str(e), "content": content[:500]})
        raise ValueError("Failed to parse the resume. Please try again or fill in your profile manually.")
