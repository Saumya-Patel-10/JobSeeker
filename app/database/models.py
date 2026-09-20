"""SQLAlchemy 2.0 ORM models.

We keep these intentionally close to the Pydantic domain models in
``app/models/`` but with relational concerns: foreign keys, indices,
timestamps, JSON columns for raw payloads.

Enum-like fields are stored as ``VARCHAR`` and validated at the Pydantic
layer; SQLite has no native ENUM type so this keeps migrations simple.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Project-wide declarative base."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512))
    industry: Mapped[str | None] = mapped_column(String(255))
    size: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)

    jobs: Mapped[list[Job]] = relationship(back_populates="company")

    __table_args__ = (UniqueConstraint("name", name="uq_company_name"),)


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    remote_type: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)

    description_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description_html: Mapped[str | None] = mapped_column(Text)

    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    salary_period: Mapped[str] = mapped_column(String(16), default="year", nullable=False)

    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    ats_source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    company: Mapped[Company] = relationship(back_populates="jobs")
    applications: Mapped[list[Application]] = relationship(back_populates="job")
    scores: Mapped[list[JobScoreRow]] = relationship(back_populates="job")
    resume_versions: Mapped[list[ResumeVersion]] = relationship(back_populates="job")

    __table_args__ = (
        Index("ix_jobs_title_company", "title", "company_id"),
        Index("ix_jobs_status", "status"),
    )


class JobScoreRow(TimestampMixin, Base):
    __tablename__ = "job_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)

    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    salary_fit: Mapped[float] = mapped_column(Float, nullable=False)
    skill_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    seniority_alignment: Mapped[float] = mapped_column(Float, nullable=False)
    location_compatibility: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    composite: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    model_used: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    job: Mapped[Job] = relationship(back_populates="scores")


class ResumeVersion(TimestampMixin, Base):
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), index=True)

    kind: Mapped[str] = mapped_column(String(16), default="tailored", nullable=False)
    template: Mapped[str] = mapped_column(String(32), default="generic", nullable=False)

    docx_path: Mapped[str | None] = mapped_column(String(1024))
    pdf_path: Mapped[str | None] = mapped_column(String(1024))
    json_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ats_score_notes: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    job: Mapped[Job | None] = relationship(back_populates="resume_versions")
    applications: Mapped[list[Application]] = relationship(back_populates="resume_version")


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    resume_version_id: Mapped[int | None] = mapped_column(ForeignKey("resume_versions.id"))

    profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(16), default="human_review", nullable=False)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(String(64))

    notes: Mapped[str | None] = mapped_column(Text)
    recruiter_name: Mapped[str | None] = mapped_column(String(255))
    recruiter_email: Mapped[str | None] = mapped_column(String(255))

    cover_letter: Mapped[str | None] = mapped_column(Text)
    confirmation_text: Mapped[str | None] = mapped_column(Text)

    job: Mapped[Job] = relationship(back_populates="applications")
    resume_version: Mapped[ResumeVersion | None] = relationship(back_populates="applications")
    events: Mapped[list[ApplicationEvent]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    answers: Mapped[list[GeneratedAnswerRow]] = relationship(back_populates="application")


class ApplicationEvent(TimestampMixin, Base):
    __tablename__ = "application_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    application: Mapped[Application] = relationship(back_populates="events")


class GeneratedAnswerRow(TimestampMixin, Base):
    __tablename__ = "generated_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), index=True)

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    approved_text: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(16), default="llm", nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application: Mapped[Application | None] = relationship(back_populates="answers")


class ApprovalCheckpoint(TimestampMixin, Base):
    __tablename__ = "approval_checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    checkpoint_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    resume_version_id: Mapped[int | None] = mapped_column(ForeignKey("resume_versions.id"))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    risks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    generated_answers: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[str | None] = mapped_column(String(64))


class BlacklistSuggestion(TimestampMixin, Base):
    __tablename__ = "blacklist_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    matched_pattern: Mapped[str | None] = mapped_column(String(255))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
