"""
Profile schema with production-grade validation.
Fields aligned with the LaTeX resume template sections.

Dates: stored as start_date + end_date + is_current.
Descriptions: stored as free text. Resume tailor converts to bullets.
"""
from pydantic import BaseModel, field_validator

MAX_STRING = 500
MAX_TEXT = 2000
MAX_EDUCATION = 10
MAX_EXPERIENCE = 20
MAX_PROJECTS = 15
MAX_SKILLS_LIST = 30
MAX_LEADERSHIP = 10


def _truncate(s: str, max_len: int) -> str:
    if not s or len(s) <= max_len:
        return s
    return s[:max_len]


def _sanitize_str(v, max_len=MAX_STRING):
    if not isinstance(v, str):
        return ""
    return _truncate(v.strip(), max_len)


def _sanitize_str_list(v, max_items=MAX_SKILLS_LIST, max_len=200):
    if not isinstance(v, list):
        return []
    return [_truncate(str(s).strip(), max_len) for s in v[:max_items] if str(s).strip()]


# ---- Sub-schemas ----

class PersonalSchema(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""

    @field_validator("name", "email", "phone", "location", "linkedin", "github", mode="before")
    @classmethod
    def sanitize(cls, v):
        return _sanitize_str(v)


class EducationItemSchema(BaseModel):
    institution: str = ""
    location: str = ""
    degree: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    details: str = ""  # coursework, GPA, honors

    @field_validator("institution", "location", "degree", "start_date", "end_date", mode="before")
    @classmethod
    def sanitize(cls, v):
        return _sanitize_str(v)

    @field_validator("details", mode="before")
    @classmethod
    def sanitize_details(cls, v):
        return _sanitize_str(v, MAX_TEXT)

    @property
    def dates_display(self) -> str:
        if self.is_current:
            return f"{self.start_date} -- Present"
        if self.start_date and self.end_date:
            return f"{self.start_date} -- {self.end_date}"
        return self.start_date or self.end_date or ""


class ExperienceItemSchema(BaseModel):
    role: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    description: str = ""  # free text — tailor agent converts to bullets

    @field_validator("role", "company", "location", "start_date", "end_date", mode="before")
    @classmethod
    def sanitize(cls, v):
        return _sanitize_str(v)

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_desc(cls, v):
        return _sanitize_str(v, MAX_TEXT)

    @property
    def dates_display(self) -> str:
        if self.is_current:
            return f"{self.start_date} -- Present"
        if self.start_date and self.end_date:
            return f"{self.start_date} -- {self.end_date}"
        return self.start_date or self.end_date or ""


class ProjectItemSchema(BaseModel):
    name: str = ""
    tech_stack: list[str] = []
    url: str = ""
    description: str = ""  # free text — tailor agent converts to bullets

    @field_validator("name", "url", mode="before")
    @classmethod
    def sanitize(cls, v):
        return _sanitize_str(v)

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_desc(cls, v):
        return _sanitize_str(v, MAX_TEXT)

    @field_validator("tech_stack", mode="before")
    @classmethod
    def sanitize_tech(cls, v):
        return _sanitize_str_list(v, 20, 100)


class LeadershipItemSchema(BaseModel):
    description: str = ""

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_desc(cls, v):
        return _sanitize_str(v, MAX_TEXT)


class SkillsCategorySchema(BaseModel):
    category: str = ""
    items: list[str] = []

    @field_validator("category", mode="before")
    @classmethod
    def sanitize(cls, v):
        return _sanitize_str(v, 100)

    @field_validator("items", mode="before")
    @classmethod
    def sanitize_items(cls, v):
        return _sanitize_str_list(v, MAX_SKILLS_LIST, 100)


class PreferencesSchema(BaseModel):
    target_roles: list[str] = []
    industries: list[str] = []

    @field_validator("target_roles", "industries", mode="before")
    @classmethod
    def sanitize(cls, v):
        return _sanitize_str_list(v)


# ---- Main Profile ----

class ProfileSchema(BaseModel):
    personal: PersonalSchema = PersonalSchema()
    education: list[EducationItemSchema] = []
    experience: list[ExperienceItemSchema] = []
    projects: list[ProjectItemSchema] = []
    skills: dict[str, list[str]] = {"technical": [], "soft": []}
    skills_categories: list[SkillsCategorySchema] = []
    leadership: list[LeadershipItemSchema] = []
    preferences: PreferencesSchema = PreferencesSchema()

    @field_validator("education", mode="before")
    @classmethod
    def limit_education(cls, v):
        return v[:MAX_EDUCATION] if isinstance(v, list) else []

    @field_validator("experience", mode="before")
    @classmethod
    def limit_experience(cls, v):
        return v[:MAX_EXPERIENCE] if isinstance(v, list) else []

    @field_validator("projects", mode="before")
    @classmethod
    def limit_projects(cls, v):
        return v[:MAX_PROJECTS] if isinstance(v, list) else []

    @field_validator("leadership", mode="before")
    @classmethod
    def limit_leadership(cls, v):
        return v[:MAX_LEADERSHIP] if isinstance(v, list) else []

    @field_validator("skills", mode="before")
    @classmethod
    def sanitize_skills(cls, v):
        if not isinstance(v, dict):
            return {"technical": [], "soft": []}
        return {
            k: _sanitize_str_list(v.get(k, []), MAX_SKILLS_LIST, 100)
            for k in ["technical", "soft"]
        }
