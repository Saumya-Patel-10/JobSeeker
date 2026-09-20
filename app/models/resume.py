"""Resume domain models.

``ResumeMaster`` is loaded from ``config/resume_master.json``.
``TailoredResume`` is what the LLM produces for a specific job.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.profile import CertificationEntry, EducationEntry, EmploymentEntry


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ProjectEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    tech: list[str] = Field(default_factory=list)
    url: HttpUrl | None = None
    bullets: list[str] = Field(default_factory=list)


class ResumeMaster(BaseModel):
    """The full superset resume — pipelines extract/rewrite from this."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    headline: str | None = None
    skills: list[str] = Field(default_factory=list)
    employment: list[EmploymentEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    """A job-specific resume produced by the tailor pipeline."""

    model_config = ConfigDict(extra="forbid")

    job_id: int | None = None
    template: Literal["backend", "ml", "generic"] = "generic"
    summary: str
    headline: str | None = None
    skills: list[str]
    employment: list[EmploymentEntry]
    education: list[EducationEntry]
    projects: list[ProjectEntry] = Field(default_factory=list)
    keywords_targeted: list[str] = Field(default_factory=list)
    ats_score_notes: str | None = None
    generated_at: datetime = Field(default_factory=_utcnow)
    model_used: str = ""
