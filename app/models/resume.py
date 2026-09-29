"""Resume model — ORM table + Pydantic config models.

``Resume``        — SQLAlchemy ORM row (stored in DB, linked to a user).
``ResumeMaster``  — Pydantic model validating ``config/resume_master.json``.
``TailoredResume``— Pydantic model for LLM-generated tailored resume output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# ---------------------------------------------------------------------------
# Guard: only import Base when SQLAlchemy is needed (avoids import errors
# in contexts where only the Pydantic models are used).
# ---------------------------------------------------------------------------
try:
    from app.db.base_class import Base as _Base  # type: ignore[import]
    _HAS_ORM = True
except Exception:
    _HAS_ORM = False


# ── Pydantic config models (used by loader, pipelines, and API) ─────────────

class EmploymentEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    company: str
    title: str
    location: str | None = None
    start: str
    end: str | None = None
    current: bool = False
    bullets: list[str] = Field(default_factory=list)
    tech: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    institution: str
    degree: str
    field: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    gpa: float | None = None
    honors: list[str] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    issuer: str | None = None
    issued: str | None = None
    expires: str | None = None
    credential_id: str | None = None
    url: str | None = None


class ProjectEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    description: str | None = None
    tech: list[str] = Field(default_factory=list)
    url: str | None = None
    bullets: list[str] = Field(default_factory=list)


class ResumeMaster(BaseModel):
    """Pydantic model for ``config/resume_master.json``."""

    model_config = ConfigDict(extra="allow")

    headline: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    employment: list[EmploymentEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    publications: list[Any] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    """LLM output model — a tailored version of ResumeMaster for a specific job."""

    model_config = ConfigDict(extra="allow")

    headline: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    employment: list[EmploymentEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


# ── SQLAlchemy ORM model (only active when DB is available) ─────────────────


class Resume(_Base):  # type: ignore[valid-type]
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # ── File references ───────────────────────────────────────────────────────
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)        # original upload
    s3_key_pdf: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # PDF version

    # ── Parsed content (cached for AI matching) ───────────────────────────────
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_json: Mapped[str | None] = mapped_column(Text, nullable=True)     # JSON array string

    # ── Style snapshot (used for cover letter matching on BASIC/PRO) ──────────
    style_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    is_master: Mapped[bool] = mapped_column(Boolean, default=False)          # primary resume
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    owner: Mapped["User"] = relationship("User", back_populates="resumes")
