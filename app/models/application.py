"""Application model — ORM table + Pydantic domain models.

``Application``       — SQLAlchemy ORM row (DB record per application attempt).
``ApplicationStatus`` — Canonical status enum (re-exported from enums for convenience).
``ApplicationMode``   — How to handle submission (re-exported from enums).
``ApplicationContext``— Pydantic model passed into every ATS adapter fill/submit call.
``FillReport``        — Result of a successful form-fill attempt.
``SubmitReport``      — Result of a submission attempt (or refusal).
``DryRunReport``      — Result of a dry-run inspection.
``GeneratedAnswer``   — A single LLM-generated answer to an application question.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Re-export enums from the canonical source so callers can import from here.
from app.models.enums import ApplicationMode, ApplicationStatus  # noqa: F401
from app.models.resume import ResumeMaster, TailoredResume
from app.models.profile import Profile

# ── Pydantic domain models ───────────────────────────────────────────────────


class GeneratedAnswer(BaseModel):
    """An LLM-generated answer to a single application question."""

    model_config = ConfigDict(extra="allow")

    question: str
    answer: str
    field_label: str | None = None
    source: str = "llm"  # "llm" | "profile" | "memory" | "user"
    confidence: float = 1.0


class FieldDescriptor(BaseModel):
    """Describes a single detected form field on an application page."""

    model_config = ConfigDict(extra="allow")

    label: str
    field_type: str = "text"   # matches FieldType enum values
    selector: str | None = None
    placeholder: str | None = None
    required: bool = False
    options: list[str] = Field(default_factory=list)   # for select/radio/checkbox
    current_value: str | None = None
    generated_answer: GeneratedAnswer | None = None


class ApplicationContext(BaseModel):
    """Everything an ATS adapter needs to fill or submit an application."""

    model_config = ConfigDict(extra="forbid")

    job_id: int
    job_url: str
    mode: ApplicationMode = ApplicationMode.human_review
    profile: Profile
    master_resume: ResumeMaster
    tailored_resume: TailoredResume | None = None
    cover_letter: str | None = None
    memory_lookup: list[GeneratedAnswer] = Field(default_factory=list)
    allow_auto: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)


class FillReport(BaseModel):
    """Result returned by an adapter after filling a form."""

    model_config = ConfigDict(extra="allow")

    job_id: int
    adapter: str
    success: bool = True
    fields_filled: int = 0
    fields_skipped: int = 0
    answers: list[GeneratedAnswer] = Field(default_factory=list)
    screenshot_path: str | None = None
    notes: list[str] = Field(default_factory=list)
    filled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SubmitReport(BaseModel):
    """Result returned by an adapter after a submit attempt."""

    model_config = ConfigDict(extra="allow")

    job_id: int
    adapter: str
    submitted: bool = False
    refused: bool = False          # True when adapter purposely blocks submit (e.g. LinkedIn)
    error: str | None = None
    confirmation_text: str | None = None
    screenshot_path: str | None = None
    submitted_at: datetime | None = None


class DryRunReport(BaseModel):
    """Result of a dry-run page inspection (no filling)."""

    model_config = ConfigDict(extra="allow")

    job_id: int
    adapter: str
    fields_detected: int = 0
    notes: list[str] = Field(default_factory=list)
    screenshot_path: str | None = None
    ran_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── SQLAlchemy ORM model ─────────────────────────────────────────────────────

try:
    from datetime import datetime as _dt

    from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.db.base_class import Base as _Base  # type: ignore[import]

    class Application(_Base):  # type: ignore[valid-type]
        __tablename__ = "applications"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
        job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
        resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id"), nullable=False)

        status: Mapped[str] = mapped_column(String(64), default="queued", nullable=False)
        celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
        error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

        match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
        tailored_resume_s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
        cover_letter_s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
        interview_questions_json: Mapped[str | None] = mapped_column(Text, nullable=True)

        ats_optimized: Mapped[bool] = mapped_column(Integer, default=False)

        applied_at: Mapped[_dt | None] = mapped_column(DateTime(timezone=True), nullable=True)
        created_at: Mapped[_dt] = mapped_column(DateTime(timezone=True), server_default=func.now())
        updated_at: Mapped[_dt] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )

        user: Mapped["User"] = relationship("User", back_populates="applications")  # type: ignore[name-defined]
        job: Mapped["Job"] = relationship("Job", back_populates="applications")  # type: ignore[name-defined]
        resume: Mapped["Resume"] = relationship("Resume")  # type: ignore[name-defined]

except Exception:
    # ORM not available in local-first SQLite path — Pydantic models above are enough.
    Application = None  # type: ignore[assignment, misc]
