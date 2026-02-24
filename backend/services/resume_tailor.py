"""
Resume Tailor Agent
===================
Takes user profile + job description → produces tailored LaTeX resume.

The template is NEVER modified. Only data is injected into {{PLACEHOLDERS}}.
LaTeX output matches the exact style from the user's reference resume.
"""
import json
from pathlib import Path

import config
from core.logging import get_logger
from services.gemini_client import generate_with_retry
from schemas.profile import ProfileSchema

logger = get_logger(__name__)

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "resume_base.tex"

TAILOR_SYSTEM_PROMPT_TEMPLATE = """You are an expert resume writer. Given a candidate's profile (with descriptions) and a target job description, convert each description into concise, impactful bullet points tailored to the target role.

CRITICAL CONSTRAINT: THE RESUME MUST FIT ON EXACTLY ONE PAGE.

BULLET LIMITS:
- Each EXPERIENCE item: exactly {exp_bullets} bullet points. Each bullet should be 150-250 characters (roughly 2 lines on a resume). Pack in details, metrics, and impact.
- Each PROJECT item: STRICTLY 2 bullet points. Each bullet MUST be under 100 characters so it fits on exactly 1 line. No exceptions.

RULES:
- Start with strong action verbs. Include metrics where possible.
- Emphasize skills, tools, and achievements that match the job description.
- Preserve TRUTHFULNESS — only reframe existing accomplishments, never invent.
- Return the SAME number of experience and project items as the input.
- BREVITY IS CRITICAL for projects. Every word must earn its place.

OUTPUT FORMAT — respond with ONLY valid JSON, no markdown:
{{
  "experience": [
    {{"role": "...", "company": "...", "location": "...", "dates": "...", "bullets": ["...", "..."]}}
  ],
  "projects": [
    {{"name": "...", "tech_stack": ["..."], "url": "...", "bullets": ["max 120 chars", "max 120 chars"]}}
  ]
}}"""


# ---- LaTeX escaping ----

def _esc(s: str) -> str:
    if not s:
        return ""
    for old, new in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                     ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                     ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        s = s.replace(old, new)
    return s


# ---- Section formatters (matching exact reference resume style) ----

def _fmt_heading(p) -> str:
    name = _esc(p.name or "Your Name")
    phone = _esc(p.phone or "")
    email = p.email or ""
    linkedin = p.linkedin or ""
    github = p.github or ""
    location = _esc(p.location or "")

    # Build LinkedIn URL
    if linkedin.startswith("http"):
        li_url = linkedin
    elif linkedin:
        li_url = f"https://www.linkedin.com/in/{linkedin}"
    else:
        li_url = "#"

    # Build GitHub URL
    if github.startswith("http"):
        gh_url = github
    elif github:
        gh_url = f"https://github.com/{github}"
    else:
        gh_url = "#"

    return (
        r"\begin{center}" "\n"
        r"    \textbf{\Huge \scshape " + name + r"} \\ \vspace{1pt}" "\n"
        r"    \small " + (phone or "---") +
        r" $|$ \href{mailto:" + email + "}{" + _esc(email) + r"} $|$" "\n"
        r"    \href{" + _esc(li_url) + r"}{LinkedIn} $|$" "\n"
        r"    \href{" + _esc(gh_url) + r"}{GitHub}" +
        (r" $|$ \small " + location if location else "") + "\n"
        r"\end{center}"
    )


def _fmt_education(edu_list) -> str:
    lines = ["  \\resumeSubHeadingListStart"]
    for e in edu_list:
        if not e.institution and not e.degree:
            continue
        # Build dates from start_date/end_date/is_current
        if e.is_current:
            dates = f"{e.start_date} -- Present" if e.start_date else "Present"
        elif e.start_date and e.end_date:
            dates = f"{e.start_date} -- {e.end_date}"
        else:
            dates = e.start_date or e.end_date or ""
        lines.append("    \\resumeSubheading")
        lines.append(f"      {{{_esc(e.institution)}}}{{{_esc(e.location or '')}}}")
        lines.append(f"      {{{_esc(e.degree)}}}{{{_esc(dates)}}}")
    lines.append("  \\resumeSubHeadingListEnd")
    return "\n".join(lines)


def _fmt_experience(experience: list[dict], max_bullets: int = 3) -> str:
    lines = ["  \\resumeSubHeadingListStart"]
    for exp in experience:
        role = _esc(exp.get("role", ""))
        dates = _esc(exp.get("dates", ""))
        company = _esc(exp.get("company", ""))
        location = _esc(exp.get("location", ""))
        bullets = exp.get("bullets", [])

        lines.append("")
        lines.append("    \\resumeSubheading")
        lines.append(f"      {{{role}}}{{{dates}}}")
        lines.append(f"      {{{company}}}{{{location}}}")
        lines.append("      \\resumeItemListStart")
        lines.append("        \\setlength\\itemsep{2pt}")
        for b in bullets[:max_bullets]:
            lines.append(f"        \\resumeItem{{{_esc(b)}}}")
        lines.append("      \\resumeItemListEnd")

    lines.append("")
    lines.append("  \\resumeSubHeadingListEnd")
    return "\n".join(lines)


def _fmt_projects(projects: list[dict], max_bullets: int = 2) -> str:
    lines = ["    \\resumeSubHeadingListStart"]
    for p in projects:
        name = _esc(p.get("name", ""))
        tech = p.get("tech_stack", [])
        tech_str = ", ".join(_esc(t) for t in tech[:8]) if tech else ""
        url = p.get("url", "") or ""
        bullets = p.get("bullets", [])

        # Build URL
        if url and not url.startswith("http"):
            url = f"https://github.com/{url}"

        heading = f"\\textbf{{{name}}}"
        if tech_str:
            heading += f" $|$ \\emph{{{tech_str}}}"

        url_part = ""
        if url:
            url_part = r"\href{" + _esc(url) + r"}{\emph{GitHub}}"

        lines.append("")
        lines.append("      \\resumeProjectHeading")
        lines.append(f"          {{{heading}}}{{{url_part}}}")
        lines.append("          \\resumeItemListStart")
        lines.append("            \\setlength\\itemsep{2pt}")
        for b in bullets[:2]:  # HARD LIMIT: always 2 bullets for projects
            # Truncate to 120 chars if Gemini exceeded
            b_str = str(b)[:100]
            lines.append(f"            \\resumeItem{{{_esc(b_str)}}}")
        lines.append("          \\resumeItemListEnd")
        lines.append("      \\vspace{-5pt}")

    lines.append("")
    lines.append("    \\resumeSubHeadingListEnd")
    return "\n".join(lines)


def _fmt_skills(profile: ProfileSchema) -> str:
    """Format skills exactly like the reference: category-based rows."""
    rows = []

    if profile.skills_categories:
        for cat in profile.skills_categories:
            if cat.items:
                items_str = ", ".join(_esc(s) for s in cat.items)
                rows.append(f"     \\textbf{{{_esc(cat.category)}}}{{: {items_str}}}")
    else:
        # Fallback: flat skills dict
        tech = profile.skills.get("technical", [])
        soft = profile.skills.get("soft", [])
        if tech:
            rows.append(f"     \\textbf{{Technical}}{{: {', '.join(_esc(s) for s in tech[:25])}}}")
        if soft:
            rows.append(f"     \\textbf{{Soft Skills}}{{: {', '.join(_esc(s) for s in soft[:15])}}}")

    if not rows:
        rows.append("     \\textbf{Skills}{: ---}")

    return (
        r"\begin{itemize}[leftmargin=0.15in, label={}]" "\n"
        r"    \small{\item{" "\n"
        + " \\\\\n".join(rows) + " \\\\\n"
        r"    }}" "\n"
        r"\end{itemize}"
    )


def _fmt_leadership(profile: ProfileSchema) -> str:
    """Format leadership as bullet list, matching reference style."""
    items = [_esc(lead.description) for lead in profile.leadership if lead.description]

    if not items:
        items.append("---")

    bullet_lines = "\n".join(f"    \\item\\small{{{it}}}" for it in items[:6])
    return (
        r"  \begin{itemize}[leftmargin=0.15in, label=$\vcenter{\hbox{\tiny$\bullet$}}$]" "\n"
        r"    \setlength\itemsep{0pt} % Tight packing" "\n"
        + bullet_lines + "\n"
        r"  \end{itemize}"
    )


# ---- One-page budget calculator ----

# Line estimates calibrated against actual LaTeX output at 11pt with aggressive margins.
# Your reference resume: 2 edu + 3 exp (3 bullets each @ 2 lines) + 3 proj (2 bullets each) +
# 5 skill rows + 3 leadership = fits exactly 1 page.
# Calibrated backwards from your actual reference resume that fits 1 page:
# Content: 2 edu + 3 exp (9 bullets total, each ~2 lines) + 3 proj (6 bullets total) +
#          5 skill rows + 3 leadership items
# Back-calculated: the page holds ~62 effective "units" with your margins/font.
_LINES_HEADING = 3
_LINES_SECTION_HEADER = 1.5
_LINES_EDU_ITEM = 2
_LINES_EXP_HEADER = 2
_LINES_PROJ_HEADER = 1.5
_LINES_SKILL_ROW = 1
_LINES_LEADERSHIP_ITEM = 1
_LINES_EXP_BULLET = 2          # each experience bullet takes ~2 printed lines
_LINES_PROJ_BULLET = 1.2       # each project bullet takes ~1 printed line
_MAX_LINES = 62                 # back-calculated from reference resume that fits


def _calculate_bullet_budget(profile_dict: dict) -> tuple[int, int]:
    """
    Calculate how many bullets per experience to fill exactly one page.
    Projects are ALWAYS 2 bullets (hard rule).
    Experience dynamically gets all remaining space.
    Returns (exp_bullets_each, 2).
    """
    PROJ_BULLETS = 2  # fixed, never changes

    n_edu = len([e for e in profile_dict.get("education", []) if e.get("institution") or e.get("degree")])
    n_exp = len([e for e in profile_dict.get("experience", []) if e.get("role") or e.get("company")])
    n_proj = len([p for p in profile_dict.get("projects", []) if p.get("name")])
    n_skills = len(profile_dict.get("skills_categories", [])) or 2
    n_lead = len([l for l in profile_dict.get("leadership", []) if l.get("description")])

    # Calculate all fixed space usage
    used = _LINES_HEADING
    used += _LINES_SECTION_HEADER * 5  # edu, exp, proj, skills, leadership sections
    used += n_edu * _LINES_EDU_ITEM
    used += n_exp * _LINES_EXP_HEADER
    used += n_proj * (_LINES_PROJ_HEADER + PROJ_BULLETS * _LINES_PROJ_BULLET)
    used += n_skills * _LINES_SKILL_ROW
    used += n_lead * _LINES_LEADERSHIP_ITEM

    remaining = _MAX_LINES - used

    if n_exp == 0 or remaining < 5:
        return (2, PROJ_BULLETS)

    # All remaining space goes to experience bullets
    exp_bullets = int(remaining / n_exp / _LINES_EXP_BULLET)
    exp_bullets = max(2, min(exp_bullets, 5))  # clamp 2-5

    logger.info("Budget calculated", extra={
        "used_lines": round(used, 1), "remaining": round(remaining, 1),
        "n_exp": n_exp, "n_proj": n_proj,
        "exp_bullets": exp_bullets, "proj_bullets": PROJ_BULLETS,
    })

    return (exp_bullets, PROJ_BULLETS)


# ---- Gemini tailoring ----

def _build_dates(item: dict) -> str:
    """Build display dates from start_date/end_date/is_current fields."""
    start = item.get("start_date", "") or item.get("dates", "")
    end = item.get("end_date", "")
    is_current = item.get("is_current", False)
    if is_current:
        return f"{start} -- Present" if start else "Present"
    if start and end:
        return f"{start} -- {end}"
    return start or end or ""


def _call_gemini_tailor(profile_dict: dict, job_description: str) -> tuple[list[dict], list[dict]]:
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    # Build payload with descriptions (not bullets) for Gemini to convert
    experience = []
    for exp in profile_dict.get("experience", []):
        experience.append({
            "role": exp.get("role", ""),
            "company": exp.get("company", ""),
            "location": exp.get("location", ""),
            "dates": _build_dates(exp),
            "description": exp.get("description", ""),
        })

    projects = []
    for proj in profile_dict.get("projects", []):
        projects.append({
            "name": proj.get("name", ""),
            "tech_stack": proj.get("tech_stack", []),
            "url": proj.get("url", ""),
            "description": proj.get("description", ""),
        })

    payload = {"experience": experience, "projects": projects}

    # Calculate dynamic bullet budget
    exp_budget, proj_budget = _calculate_bullet_budget(profile_dict)
    logger.info("Bullet budget", extra={"exp_bullets": exp_budget, "proj_bullets": proj_budget,
                                          "n_exp": len(experience), "n_proj": len(projects)})

    system_prompt = TAILOR_SYSTEM_PROMPT_TEMPLATE.format(
        exp_bullets=exp_budget, proj_bullets=proj_budget
    )

    prompt = f"""CANDIDATE PROFILE:
{json.dumps(payload, indent=2)}

TARGET JOB DESCRIPTION:
{job_description}

Convert descriptions into tailored bullet points. Experience: {exp_budget} bullets each. Projects: {proj_budget} bullets each. Return JSON only."""

    content = generate_with_retry(
        contents=prompt,
        system_instruction=system_prompt,
        temperature=0.3,
    )

    if "```" in content:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]

    try:
        data = json.loads(content)
        experience = data.get("experience", payload["experience"])
        projects = data.get("projects", payload["projects"])

        # Preserve URLs from original
        orig_projects = profile_dict.get("projects", [])
        for i, p in enumerate(projects):
            if isinstance(p, dict) and i < len(orig_projects):
                orig = orig_projects[i] if isinstance(orig_projects[i], dict) else {}
                if not p.get("url") and orig.get("url"):
                    p["url"] = orig["url"]
                if not p.get("tech_stack") and orig.get("tech_stack"):
                    p["tech_stack"] = orig["tech_stack"]

        return experience, projects
    except json.JSONDecodeError:
        logger.warning("Gemini returned invalid JSON, using original bullets")
        return payload["experience"], payload["projects"]


# ---- Main entry ----

def generate_tailored_resume(profile: ProfileSchema, job_description: str) -> str:
    """Generate a job-tailored LaTeX resume. Template is NEVER modified."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    profile_dict = profile.model_dump()

    # Tailor via Gemini
    job_ctx = job_description.strip() or "General software engineering role"
    try:
        experience, projects = _call_gemini_tailor(profile_dict, job_ctx)
    except Exception as e:
        logger.exception("Gemini tailoring failed, using original")
        experience = profile_dict.get("experience", [])
        projects = profile_dict.get("projects", [])

    # Ensure projects have bullets (convert legacy description field)
    for p in projects:
        if not p.get("bullets"):
            desc = p.get("description", "")
            p["bullets"] = [s.strip() for s in str(desc).split(". ") if s.strip()][:3] or ["---"]

    # Calculate budget for one-page fit
    exp_budget, proj_budget = _calculate_bullet_budget(profile_dict)

    # Fill template
    latex = template
    latex = latex.replace("{{HEADING}}", _fmt_heading(profile.personal))
    latex = latex.replace("{{EDUCATION}}", _fmt_education(profile.education))
    latex = latex.replace("{{EXPERIENCE}}", _fmt_experience(experience, max_bullets=exp_budget))
    latex = latex.replace("{{PROJECTS}}", _fmt_projects(projects, max_bullets=proj_budget))
    latex = latex.replace("{{SKILLS}}", _fmt_skills(profile))
    latex = latex.replace("{{LEADERSHIP}}", _fmt_leadership(profile))

    return latex
